from UnleashClient import UnleashClient

client = UnleashClient(
    url="https://gitlab.com/api/v4/feature_flags/unleash/46289363",
    app_name="braudu",
    instance_id =  'CV6xDsbk8P4ugBCz8fj_'
)

client.initialize_client() 
print("Client initialized successfully " )

print(client.is_enabled("linkedin-current-company-verification"))