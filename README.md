![Ethereal logo](./docs/images/ethereal_cat.png)

## Ethereal

[![docs](https://readthedocs.org/projects/ethereal/badge/?version=latest)](https://ethereal.readthedocs.io/en/latest/?badge=latest)

Ethereal is a lightweight wrapper around the [Web3](https://web3py.readthedocs.io/en/stable/web3.main.html#web3.Web3) class that simplifies
working with Ethereum smart contracts.

To use it, simply create a regular [Web3](https://web3py.readthedocs.io/en/stable/web3.main.html#web3.Web3) instance and write `w3 = Ethereal(w3)`.
Then, you can use w3 as usual, but with additional methods
accessible under the `e` property.

For example, you can call `w3.e.get_abi("0x...")` or
`w3.e.list_events("0x...", "Mint", "2023-01-01", "2023-02-14")`.

For more available methods, please refer to the :class:`ethereal.facade.EtherealFacade` class.

### Example

```python

        from web3.auto import w3
        from ethereal import Ethereal
        from ethereal import load_provider_from_uri

        # If WEB3_PROVIDER_URI env is not set, uncomment the lines below
        # w3 = Web3(load_provider_from_uri("https://alchemy.com/..."))

        w3 = Ethereal(w3)

        ADDRESS = "0xB0B195aEFA3650A6908f15CdaC7D92F8a5791B0B"
        print(w3.e.list_events(ADDRESS))
        # Lists event signatures for the contract at ADDRESS

        events = w3.e.get_events(ADDRESS, "Transfer", "2023-01-01", "2023-02-14")
        # Gets all Transfer events for the contract at ADDRESS between 2023-01-01 and 2023-02-14
        print(events[:10])
```

### Install

```
pip install ethereal
```
