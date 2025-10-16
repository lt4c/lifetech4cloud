from app.main import run_db_migrations, init_admin, app

run_db_migrations()
print('migrations ok')

init_admin(app)
print('init_admin ok')

