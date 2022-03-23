from user_cli import YADDBClient as cli

def tryWriteExample(key,value,content_type,encoding):
    #Run a server with the following command
    #$ python run_frontend.py -H 127.0.0.1 -p 80

    #create a client to use de databse
    some_client=cli('127.0.0.1',80)

    #Write to Database
    written=some_client.write(key.encode(),value.encode(),content_type,encoding) #key and value MUST be Bytes
    if written:
        print(value,' succesfully written to database')

def tryReadExample(key):
    some_client=cli('127.0.0.1',80)
     
    #Read from Database
    read=some_client.read(key.encode()) #key MUST be Bytes
    if read:
        print(key,' stores: [',read,']')



def test():
    key=0 #Needs to be bytes
    value='Hello World' # Needs to be bytes
    print(my_db_client.host,my_db_client.port)
    #Set Value 'Hello World' to Database in key 0
    print(my_db_client.write(key.to_bytes(2, 'big'),value.encode(),'text/plain','UTF-8'))
    print(my_db_client.read(key.to_bytes(2, 'big')))

    #Second Test
    key='my_awesome_key'
    value=1212

    print(my_db_client.write(key.encode(),value.to_bytes(2, 'big'),'text/plain','UTF-8'))
    print(my_db_client.read(key.encode()))



##Test
if __name__ == '__main__':
    my_db_client=cli('127.0.0.1',80)

    #Uncomment to run an example of using the methods from your own code
    tryWriteExample('some_key','some_value','text/plain','UTF-8') 
    tryReadExample('some_key') 

    #Simple Test set
    #test()

