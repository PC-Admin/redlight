# redlight

<p align="left">
  <img src="https://code.glowers.club/PC-Admin/redlight/logo/redlight_logo.jpg" width="480" alt="redlight logo">
</p>

_"The red light means stop!"_

An advanced abuse management tool. It's a Synapse module that allows server owners to either run a "redlight server", or to act as a "redlight client" to prevent their own users from accessing abusive rooms. It's designed to block child sexual abuse material (CSAM) and other abusive content on the Matrix network. 

This software attempts to resolve the complex problem of how to share pointers to rooms containing abusive content in order to block or report activity. These room lists are sensitive and sharing them can not only aid people in blocking this content but also direct bad actors to said content.

The goal of this tool is to simply block this content as efficiently as possible across many small-medium sized servers.


## Features

    Easy, setup for homeserver owners via Synapse Module
    Private, hashing is used to prevent redlight clients from sharing room_ids with redlight servers
    Decentralised, many people can run redlight servers with their own blocking policies, redlight clients are free to pick a provider
    Safe, access restrictions and ratelimiting are used to guard the content of rdlist


## How it Works

...

For a more detailed description of how it will work please consult the [Technical Specification](./technical_spec.md).

**Coming soon...**


## License

This project is licensed under the MIT License.


## Contributing

We warmly welcome contributors who are interested in improving Matrix Lantern. Whether you're fixing bugs, improving documentation, or proposing new features, your efforts are greatly appreciated. Please ensure that new contributions follow our [Style Guide](./style_guide.md).


## Acknowledgements

Redlight is a community-driven project aimed at protecting the Matrix network's users from harmful content. Our thanks go out to the Matrix network, Glowers Club, and all our contributors who make this project possible.


## Roadmap

1) Get a basic prototype working.
