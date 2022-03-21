# Distributed Key Value Database in Python

A simple tpy implementation of a distributed key value database in python for the Special Topics on Telematics course for Systems Engineering at Universidad EAFIT Colombia.

## Authors
- Simón Flórez Silva (sflorezs1@eafit.edu.co)

## Requirements
- This program was designed to run in `python3.10` but feel free to try and modify it to run on other versions.

## Design

### Key-Value pair format
Similar to the way we store a file in any kind of storage, we must supply a name, a content type, and the content itself.

Every item that is stored in the database must specify the datatype for both its key and value and for the later it is also required to specify the encoding of the data.

```json
{
    "${key}": {
        "content_type": "{*MIMEType}",
        "encoding": "{*some_encodings}",
        "value": "whatever value you want to send encoded"
    }
}
```

It is important to clarify that all those attributes are there only for data manipulation in the applications that use this database, **the system will not interpret the data types**.

### API

The system will use the WEB middleware over the HTTP protocol using a REST-like API.

#### Messages
HTTP methods:
- **GET:** To query for all the key value pairs in the database:
    ```bash
    curl -GET http://server:8080/
    ```
    ```json
    "data": [
        {
            "${key}": {
                "content_type": "{*MIMEType}",
                "encoding": "{*some_encodings}",
                "value": "whatever value you want to send encoded"
            }
        },
        ...
        {
            "${key}": {
                "content_type": "{*MIMEType}",
                "encoding": "{*some_encodings}",
                "value": "whatever value you want to send encoded"
            }
        },
    ]
    ```

- **POST:** To make more specific queries by key:
    ```bash
    curl -X POST http://server:8080/ -H "Content-Type: application/json" -d '${key}'
    ```
    ```json
    {
        "${key}": {
            "content_type": "{*MIMEType}",
            "encoding": "{*some_encodings}",
            "value": "whatever_value_you_asked_for"
        }
    }
    ```

    Although you cannot do ranged queries, you may query for multiple keys.

    ```bash
    curl -X POST http://server:8080/ -H "Content-Type: application/json" -d '[{"content_type": "{*MIMEType}", "value": "whatever_key_you_want_to_fetch"}, {"content_type": "{*MIMEType}", "value": "whatever_key_you_want_to_fetch"}]'
    ```
    ```json
    [
        {
            "${key}": {
                "content_type": "{*MIMEType}",
                "encoding": "{*some_encodings}",
                "value": "whatever_value_you_asked_for"
            }
        },
        {
            "${key}": {
                "content_type": "{*MIMEType}",
                "encoding": "{*some_encodings}",
                "value": "whatever_value_you_asked_for"
            }
        }
    ]
    ```
- **PUT:**
    ```bash
    curl -X PUT http://server:8080/ -H "Content-Type: application/json" -d '{"content_type": "{*MIMEType}", "encoding": "{*some_encodings}", "value": "whatever_key_you_want_store"}'
    ```
    ```json
    {
        "${key}": {
            "content_type": "{*MIMEType}",
            "encoding": "{*some_encodings}",
            "value": "whatever_key_you_want_store"
        }
    }
    ```

    You may also insert many values in one put request.

    ```bash
    curl -X PUT http://server:8080/ -H "Content-Type: application/json" -d '[{"content_type": "{*MIMEType}", "encoding": "{*some_encodings}", "value": "whatever_key_you_want_store"}, {"content_type": "{*MIMEType}", "encoding": "{*some_encodings}", "value": "whatever_key_you_want_store"}]'
    ```
    ```json
    [
        {
            "${key}": {
                "content_type": "{*MIMEType}",
                "encoding": "{*some_encodings}",
                "value": "whatever_key_you_want_store"
            }
        },
        {
            "${key2}": {
                "content_type": "{*MIMEType}",
                "encoding": "{*some_encodings}",
                "value": "whatever_key_you_want_store"
            }
        }
    ]
    ```
