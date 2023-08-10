
# Technical Spec

This document gives a detailed summary about how Redlight will work.


## Definitions

Redlight List - A comprehensive list of abusive rooms on the Matrix network, abusive rooms are assigned a 'report_id' for identification as well as multiple 'tags' that describe the infringing content in said room.

Tags - Content tags that describe the type of abusive material found in a room, for example 'csam', 'lolicon' or 'terrorism'.

Redlight Server - Will be trusted homeservers that are modified, they'll cache the Redlight list in memory while providing an API interface to "Redlight clients". Redlight servers will pick their own "content tags" that they are filtering, which by extension will allow clients to pick a level of filtering that suits them.

Redlight Client - Will be untrusted homeservers that are whitelisted by their desired Redlight server. When a user on a client homeserver attempts to join a room, the hash of the room_id will be sent to the redlight server, which will confirm or deny if the room is abusive, the client then denies the user entry to that room if it is flagged.


## The Core Issue

You might be wondering, why not just release a list of hashes of these room_ids and openly let people filter them?

Anything that can be used to identify abusive content can be used to identify abusive content ultimately. It's why access to these tools is typically so restricted. The problem isn’t that the hashes could be reversed, its that the hashes can be used to identify the abuse content.

Imagine if you have 100 room_ids and you know 1 is abusive, well you could us an openly distributed hash-list to find that content and do the right thing and block it. Or you could use it to locate that content a lot faster to consume it and break the law with it.

This repository attempts to be a solution to this problem.


## Chain of Trust

If distributing a hash-list openly is dangerous, the simplest way to make it safe to close up the distribution of it.

With Redlight only trusted parties will be allowed to run "redlight servers" and they will only accept requests from "redlight clients" who they have explicitly whitelisted.

This creates a chain of trust where each party using this system must be accountable and can have their access revoked by the party "above" them if foul play is detected.


## Securing the Redlight List

The following methods will be used to secure the redlight list:

- Avoid writing the redlight list to disk, redlight servers will simply pull the latest copy and store it in memory only.
- Whitelisting clients, redlight servers will only serve approved clients.
- Ratelimiting the amount of requests, if a client is requesting too many rooms in a specified timeframe their access will be automatically cut-off, forcing them to ask their redlight server to re-enable them.
- Ratelimiting the amount of hits, if a client is finding too many abusive rooms in a specified timeframe their access will be automatically cut-off, forcing them to ask their redlight server to re-enable them.


# Other Design Goals

Blocking not monitoring, to avoid scope creep the point of this system will only be to block access to known abusive rooms.

Client homeserver privacy, by double hashing room_ids before sending them to redlight servers analysis and collection about the rooms accessed by a redlight clients users becomes unfeasible.

Config-driven and stateless, ideally redlight clients and servers will be "stateless", so no data will persist between reboots and their behaviour will be defined entirely in configuration files.


## LJS-4.draft: Abuse Lookup API V1

The following section specifies a http service which may be used to identify known abuse rooms on Matrix.

All documented endpoints require a bearer token supplied in the `Authorization` header.

### **PUT** `/_matrix/loj/v1/abuse_lookup`

The `abuse_lookup` endpoint returns if the supplied `room_id` is reported to contain a filtered tag in Redlight List. The endpoint will
return either `200 OK` to signify a match or `204 No Content` to signify no match.

- `room_id_hash:` String. A valid Room ID that has been hashed twice with sha256

```js
{
    "room_id_hash": "962c56a12d861d1921073916db9a1fb47ccc7887d3199690f1de156e57cac709"
}
```

---

- `error:` Dict or Null. If exists, the request has failed
  - `errcode:` String. Error code
  - `error:` String. Error message
- `report_id:` String or Null. If exists, the report id associated with the room.

```js
{
    "error": null,
    "report_id": "b973d82a-6932-4cad-ac9f-f647a3a9d204",
}
```
