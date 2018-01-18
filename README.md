# Python binds for Melissa Climate

This is an unofficial wrapper for melissa web api: http://seemelissa.com/en

[Coffee fundraiser](https://paypal.me/pools/c/8177s58qSX)

### Installing

```
pip install py-melissa-climate
```

```
python
>>> from melissa import Melissa
>>> m = Melissa(username="email_adress", password="password")
>>> m.fetch_devices()
{'********': {'user_id': 1, 'serial_number': '********', 'mac': '********', 'firmware_version': 'V1SHTHF', 'name': 'Melissa ********', 'type': 'melissa', 'room_id': None, 'created': '2016-07-06 18:59:46', 'id': 1, 'online': True, 'brand_id': 1, 'controller_log': {'temp': 25.4, 'created': '2018-01-06T10:12:16.249Z', 'raw_temperature': 28188, 'humidity': 18.5, 'raw_humidity': 12862}, '_links': {'self': {'href': '/v1/controllers'}}}}
```

## Running the tests

WIP

### And coding style tests

We use flake8

```
pip install flake8
```
```
flake8 melissa
```

## Built With

* [requests](http://docs.python-requests.org/en/master/)

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/kennedyshead/py-melissa-climate/tags). 

## Authors

* **Magnus Knutas** - *Initial work* - [kennedyshead](https://github.com/kennedyshead)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Melissa dev team who made a great API
* Home-assistant.io for the inspiration to write this

