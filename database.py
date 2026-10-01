import aiosqlite

DB_NAME = "leads.db"


async def init_db():
  async with aiosqlite.connect(DB_NAME) as db:
    await db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                service TEXT,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    await db.commit()


async def add_lead(name: str, phone: str, service: str, username: str):
  async with aiosqlite.connect(DB_NAME) as db:
    await db.execute(
        """
            INSERT INTO leads (name, phone, service, username)
            VALUES (?, ?, ?, ?)
        """,
        (name, phone, service, username),
    )
    await db.commit()


async def get_all_leads():
  async with aiosqlite.connect(DB_NAME) as db:
    async with db.execute("""
            SELECT id, name, phone, service, username, created_at 
            FROM leads 
            ORDER BY id DESC
        """) as cursor:
      return await cursor.fetchall()

async def get_leads_count() -> int:
    """Получение общего количества заявок"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM leads") as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0