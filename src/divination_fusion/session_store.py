from __future__ import annotations 

from collections import defaultdict 
from dataclasses import asdict 
import json 
from pathlib import Path 
import queue 
import sqlite3 
import threading 
from typing import Any ,Optional 

from divination_fusion .models import BattleEvent ,SessionRecord ,now_iso 

class SessionStore :
    def __init__ (self ,root :Path |str ="runs/sessions",database_path :Path |str ="runs/sessions.sqlite3")->None :
        self .root =Path (root )
        self .root .mkdir (parents =True ,exist_ok =True )
        self .database_path =Path (database_path )
        self .database_path .parent .mkdir (parents =True ,exist_ok =True )
        self ._lock =threading .Lock ()
        self ._subscribers :dict [str ,list [queue .Queue [BattleEvent ]]]=defaultdict (list )
        self ._init_db ()

    def create_session (
    self ,
    *,
    session_id :str ,
    request_payload :dict [str ,Any ],
    auth_mode :str ,
    )->SessionRecord :
        created_at =now_iso ()
        record =SessionRecord (
        session_id =session_id ,
        status ="queued",
        created_at =created_at ,
        updated_at =created_at ,
        request_payload =request_payload ,
        auth_mode =auth_mode ,
        run_dir =str (self .session_dir (session_id )),
        )
        session_dir =self .session_dir (session_id )
        session_dir .mkdir (parents =True ,exist_ok =True )
        (session_dir /"request.json").write_text (
        json .dumps (request_payload ,ensure_ascii =False ,indent =2 ,sort_keys =True ),
        encoding ="utf-8",
        )
        with self ._connect ()as conn :
            conn .execute (
            """
                INSERT INTO sessions (
                    session_id, status, created_at, updated_at, auth_mode,
                    request_json, snapshot_json, report_json, run_dir
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
            session_id ,
            record .status ,
            record .created_at ,
            record .updated_at ,
            auth_mode ,
            json .dumps (request_payload ,ensure_ascii =False ),
            json .dumps (record .snapshot ,ensure_ascii =False ),
            None ,
            record .run_dir ,
            ),
            )
        return record 

    def session_dir (self ,session_id :str )->Path :
        return self .root /session_id 

    def subscribe (self ,session_id :str )->queue .Queue [BattleEvent ]:
        subscriber :queue .Queue [BattleEvent ]=queue .Queue ()
        with self ._lock :
            self ._subscribers [session_id ].append (subscriber )
        return subscriber 

    def unsubscribe (self ,session_id :str ,subscriber :queue .Queue [BattleEvent ])->None :
        with self ._lock :
            subscribers =self ._subscribers .get (session_id ,[])
            if subscriber in subscribers :
                subscribers .remove (subscriber )
            if not subscribers and session_id in self ._subscribers :
                self ._subscribers .pop (session_id ,None )

    def append_event (
    self ,
    *,
    session_id :str ,
    event_type :str ,
    payload :dict [str ,Any ],
    issue_id :Optional [str ]=None ,
    round_index :Optional [int ]=None ,
    )->BattleEvent :
        created_at =now_iso ()
        with self ._connect ()as conn :
            seq =conn .execute (
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM events WHERE session_id = ?",
            (session_id ,),
            ).fetchone ()[0 ]
            conn .execute (
            """
                INSERT INTO events (session_id, seq, event_type, issue_id, round_index, created_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
            (
            session_id ,
            seq ,
            event_type ,
            issue_id ,
            round_index ,
            created_at ,
            json .dumps (payload ,ensure_ascii =False ),
            ),
            )
        event =BattleEvent (
        seq =seq ,
        session_id =session_id ,
        event_type =event_type ,
        created_at =created_at ,
        payload =payload ,
        issue_id =issue_id ,
        round_index =round_index ,
        )
        event_path =self .session_dir (session_id )/"events.jsonl"
        with event_path .open ("a",encoding ="utf-8")as handle :
            handle .write (json .dumps (asdict (event ),ensure_ascii =False )+"\n")
        with self ._lock :
            for subscriber in self ._subscribers .get (session_id ,[]):
                subscriber .put (event )
        return event 

    def list_events (self ,session_id :str )->list [BattleEvent ]:
        with self ._connect ()as conn :
            rows =conn .execute (
            """
                SELECT seq, event_type, issue_id, round_index, created_at, payload_json
                FROM events
                WHERE session_id = ?
                ORDER BY seq ASC
                """,
            (session_id ,),
            ).fetchall ()
        return [
        BattleEvent (
        seq =row [0 ],
        session_id =session_id ,
        event_type =row [1 ],
        issue_id =row [2 ],
        round_index =row [3 ],
        created_at =row [4 ],
        payload =json .loads (row [5 ]),
        )
        for row in rows 
        ]

    def update_snapshot (
    self ,
    *,
    session_id :str ,
    status :Optional [str ]=None ,
    snapshot :Optional [dict [str ,Any ]]=None ,
    report :Optional [dict [str ,Any ]]=None ,
    )->SessionRecord :
        existing =self .get_session (session_id )
        updated_status =status or existing .status 
        updated_snapshot =snapshot if snapshot is not None else existing .snapshot 
        updated_report =report if report is not None else existing .report 
        updated_at =now_iso ()
        with self ._connect ()as conn :
            conn .execute (
            """
                UPDATE sessions
                SET status = ?, updated_at = ?, snapshot_json = ?, report_json = ?
                WHERE session_id = ?
                """,
            (
            updated_status ,
            updated_at ,
            json .dumps (updated_snapshot ,ensure_ascii =False ),
            json .dumps (updated_report ,ensure_ascii =False )if updated_report is not None else None ,
            session_id ,
            ),
            )
        if snapshot is not None :
            (self .session_dir (session_id )/"snapshot.json").write_text (
            json .dumps (updated_snapshot ,ensure_ascii =False ,indent =2 ,sort_keys =True ),
            encoding ="utf-8",
            )
        if report is not None :
            (self .session_dir (session_id )/"report.json").write_text (
            json .dumps (updated_report ,ensure_ascii =False ,indent =2 ,sort_keys =True ),
            encoding ="utf-8",
            )
        return self .get_session (session_id )

    def list_sessions (self )->list [SessionRecord ]:
        with self ._connect ()as conn :
            rows =conn .execute (
            """
                SELECT session_id, status, created_at, updated_at, auth_mode, request_json, snapshot_json, report_json, run_dir
                FROM sessions
                ORDER BY created_at DESC
                """
            ).fetchall ()
        return [self ._record_from_row (row )for row in rows ]

    def get_session (self ,session_id :str )->SessionRecord :
        with self ._connect ()as conn :
            row =conn .execute (
            """
                SELECT session_id, status, created_at, updated_at, auth_mode, request_json, snapshot_json, report_json, run_dir
                FROM sessions
                WHERE session_id = ?
                """,
            (session_id ,),
            ).fetchone ()
        if row is None :
            raise KeyError (session_id )
        return self ._record_from_row (row )

    def _record_from_row (self ,row :tuple [Any ,...])->SessionRecord :
        report =json .loads (row [7 ])if row [7 ]else None 
        return SessionRecord (
        session_id =row [0 ],
        status =row [1 ],
        created_at =row [2 ],
        updated_at =row [3 ],
        auth_mode =row [4 ],
        request_payload =json .loads (row [5 ]),
        snapshot =json .loads (row [6 ]),
        report =report ,
        run_dir =row [8 ],
        )

    def _init_db (self )->None :
        with self ._connect ()as conn :
            conn .execute (
            """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    auth_mode TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    report_json TEXT,
                    run_dir TEXT NOT NULL
                )
                """
            )
            conn .execute (
            """
                CREATE TABLE IF NOT EXISTS events (
                    session_id TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    issue_id TEXT,
                    round_index INTEGER,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY (session_id, seq)
                )
                """
            )

    def _connect (self )->sqlite3 .Connection :
        conn =sqlite3 .connect (self .database_path ,check_same_thread =False )
        conn .execute ("PRAGMA journal_mode=WAL")
        return conn 
