import requests

# Making a put request
response = requests.get('https://api.github.com', headers={'Connection': 'close'})

# print response
print(response)
print(response.status_code)
# closing the connection
response.close()

# Check if this gets execeuted
print("Connection Closed")
print(response)