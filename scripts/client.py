import httpx
import asyncio

class WebClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        self.token = None

    async def login(self, username, password):
        response = await self.client.post(
            "/auth/jwt/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("Login successful")
            # After successful login, get user info
            await self.get_user_info()
        else:
            print(f"Login failed: {response.text}")

    async def get_user_info(self):
        if not self.token:
            print("Not authenticated. Cannot get user info.")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        response = await self.client.get("/users/me", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            print(f"User Info: {user_info}")
            print(f"Credits: {user_info.get('credits')}")
        else:
            print(f"Failed to get user info: {response.text}")

    async def get_sum(self, a, b):
        if not self.token:
            print("Not authenticated")
            return

        response = await self.client.post(
            "/api/sum",
            json={"a": a, "b": b},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        if response.status_code == 200:
            print(f"Sum result: {response.json()['result']}")
        else:
            print(f"Sum failed: {response.text}")

    async def close(self):
        await self.client.aclose()

async def main():
    # Use 'nginx' hostname when running inside docker network
    client = WebClient(base_url="http://nginx:80")
    # Replace with actual credentials after creating a user
    await client.login("admin@example.com", "Admin123") 
    await client.get_sum(10, 20)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
