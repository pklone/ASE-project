class AuthenticationConnectorDBMock:

    def __init__(self):

        self.admin = [
            {
            "uuid": "1e785a5dd-7fdd-483f-93b3-b84ecaa62683",
            "username": "admin",
            "password_hash": "$2b$12$QnbxGRl6jVTzt.fbksJWVuITmX4832AnfF1uSx00hZSsDBgjXDxcO",
            }
        ]

    def getAdminByUsername(self, admin_username):

        for admin in self.admin:
            if admin['username'] == admin_username:
                return admin

        raise ValueError('Invalid credentials')
        