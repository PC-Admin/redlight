
# Technical Spec

This document gives a detailed summary about how Redlight will work.


## Definitions

Source List - A comprehensive list of abusive rooms on the Matrix network, abusive rooms are assigned a 'report_id' for identification as well as multiple 'tags' that describe the infringing content in said room.

Tags - Content tags that describe the type of abusive material found in a room, for example 'csam', 'lolicon' or 'terrorism'.

Redlight Server - Will be trusted homeservers that are modified, they'll cache the source list in memory while providing an API interface to "Redlight clients". Redlight servers will pick their own "content tags" that they are filtering, which by extension will allow clients to pick a level of filtering that suits them.

Redlight Client - Will be untrusted homeservers that are whitelisted by their desired Redlight server. When a user on a client homeserver attempts to join a room, the hash of the room_id will be sent to the redlight server, which will confirm or deny if the room is abusive, the client then denies the user entry to that room if it is flagged.


## The Core Issue

You might be wondering, why not just release a list of these room_ids (or their hashes) and openly let people filter them?

Ultimately anything that can be used to identify abusive content can be used to identify abusive content. It's why access to these tools is typically so restricted. The problem isn’t that the hashes could be reversed, it's that the hashes can be used to identify the abuse content.

Imagine if you have 100 room_ids and you know 1 is abusive, well you could us an openly distributed hash-list to find that content and do the right thing and block it. Or you could use it to locate that content a lot faster to consume it and break the law with it.

The redlight system attempts to be a solution to this problem.


## Chain of Trust

If distributing a hash-list openly is dangerous, the simplest way to make it safe to close up the distribution of it.

With Redlight only trusted parties will be allowed to run "redlight servers" and they will only accept requests from "redlight clients" who they have explicitly whitelisted.

This creates a chain of trust where each party using this system must be accountable and can have their access revoked by the party "above" them if foul play is detected.


## Securing the Source List

The following methods will be used to secure the source list:

- Avoid writing the source list to disk, redlight servers will simply pull the latest copy of the source list and store it in memory only.
- Whitelisting clients, redlight servers will only serve approved redlight clients, filtering requests by their IP.
- Ratelimiting the amount of requests, if a client homeserver or user is making too many requests the server or user in question will be cut off from the redlight server. (It will start throwing errors with every request.)
- Ratelimiting the amount of hits, if a clients user is finding too many abusive rooms in a specified timeframe that account will be "frozen", this means the redlight server will return an error (deny access) to every future join request that user account makes.


## Account Freezes

If a user_id attempts to access an abusive room 3 or more times the redlight server will start throwing errors for every future join request made by that account. This effectively "freezes" the user account and prevents any further illicit activity. It also prevents the user from reverse engineering the source list by attempting to enter many abusive rooms.

Freezes on accounts are performed by the redlight server, to unfreeze an account a request needs to be made by the redlight client to their redlight server.


## Real-time Alerting

The redlight client module will alert the homeserver owners via an "alert room", where notifications of the following will be sent:
- If a user attempts to enter an abusive room and is denied access.
- If a users account has been frozen by the redlight server.

This allows homeserver owners and moderators to act quickly in response to these incidents.


## Other Design Goals

Blocking not monitoring, to avoid scope creep the point of this system will only be to block access to known abusive rooms. Further monitoring and reporting of any users entering abusive rooms should be performed by the owners of that homeserver. (The redlight client.)

Client homeserver privacy, by double hashing the user_ids and room_ids before sending them to redlight server, analysis and collection about the rooms accessed by a redlight clients users is limited.

~~Config-driven and stateless, ideally redlight clients and servers will be "stateless", so no data will persist between reboots and their behaviour will be defined entirely in configuration files.~~ A database is probably needed for redlight servers.


## LJS-4.draft: Abuse Lookup API V1

The following section specifies a http service which may be used to identify known abuse rooms on Matrix.

All documented endpoints require a bearer token supplied in the `Authorization` header.

### **PUT** `/_matrix/loj/v1/abuse_lookup`

The `abuse_lookup` endpoint returns if the supplied `room_id` is reported to contain a filtered tag in Redlight List. The endpoint will
return either `200 OK` to signify a match or `204 No Content` to signify no match.

- `room_id_hash:` String. A valid Room ID that has been hashed twice with sha256.
- `user_id_hash:` String. A valid User ID that has been hashed twice with sha256.
- `api_token:` String. A 40 digit alphanumeric token used for endpoint authentication.

```js
{
    "room_id_hash": "5dd9968ad279b8d918b1340dde1923ed0b99f59337f4905188955bf0f1d51d9f",
    "user_id_hash": "6123512760887c37bb7b550a1a3caa8b8cd954706f4cc7fe934cb42611132627",
    "api_token": "Um05ULjUngjVbibdgtipo96VUSrEexOi8z7F8HfK"
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


## Unanswered Questions

- How many join requests from a user is abnormal?

More then 10 join requests in a minute might seem suspicious... (What about bots?)

- How many join requests from a redlight client homeserver is abnormal?

- How many join requests can a redlight server even process?

- What other methods (besides IP) could be used to restrict requests from redlight client homeservers?

API tokens, certificate-based authentication, or domain whitelisting?

API tokens seems like the move.

- What other methods could be used to secure the source list and prevent interception/leaking?

TPM/secure enclaves?
Encrypted in memory?
