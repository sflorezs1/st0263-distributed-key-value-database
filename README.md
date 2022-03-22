# Distributed Key Value Database in Python

A simple tpy implementation of a distributed key value database in python for the Special Topics on Telematics course for Systems Engineering at Universidad EAFIT Colombia.

## Authors
- Simón Flórez Silva (sflorezs1@eafit.edu.co)
- Jhoan Stiven Ruiz Arias ()
- Juan José Madrigal Palacio ()
- Adrián Alberto Gutiérrez Leal (aagutierrl@eafit.edu.co)

## Requirements
- This program was designed to run in `python3.10` but feel free to try and modify it to run on other versions.
- Python libraries:
    - `mmh3`
    - `numpy`

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
- **POST:** To make queries by key:
    ```bash
    curl -X POST http://server:8080/ -H "Content-Type: application/octet-stream" -d '${key}'
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
- **PUT:** Create an entry. One caveat, we are using bytes for the keys, which is not a datatype accepted by json, hence any key sent through this method should be transformed into a hex string first, in the server side, it will be decoded as bytes again.
    ```bash
    curl -X PUT http://server:8080/ -H "Content-Type: application/json" -d '{"key": "90219201f2","content_type": "{*MIMEType}", "encoding": "{*some_encodings}", "value": "whatever_key_you_want_store"}'
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

**Note:** We do not allow querying for all data as it would be horribly expensive in both network and disk requirements! Ranged queries are also out of reach for this project as we did not implement secondary keys!

## **Architecture**

### Front-End Server

We use a client-facing server to hide the distributed nature of the database. This server will receive every request from the client and will request the required data from the backend distributed database. It will use a C/S architecture to communicate with both the backend and the client. This component will also work as a router server.

### DB implementation

The db will be statically partitioned into a given set of slave machines running the backend db software. Each slave machine will have a set of followers that will replicate its data (with eventual consistency in mind!).

As for the storage of the key-value pairs, the db software uses a LSMTree (Log Structured Merge Tree) with two levels:
- **0. Memory:** In the form of a memtable implemented with [Red Black Trees](https://en.wikipedia.org/wiki/Red%E2%80%93black_tree).
- **1. Disk:** In the form of many segment files, storing the memtable as an SSTable (Sorted String Table) in disk after the threshold of memory (1mb by default) is exceeded.

Searching for a value that is not in memory will require to read the segments in disk, for that we will make use of an index in the form of yet another Red Black Tree. And to determine if a given key is stored in the specific segment we use a probabilistic data structure called [Bloom Filter](https://www.youtube.com/watch?v=em2j7sLhoyI). 