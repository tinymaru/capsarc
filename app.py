from flask import Flask
from user import index,reset_password_request, home, browse, search, project_details, about, about_us, user_profile, user_library, save_project, delete_project, basename_filter
from authentication import user_register, admin_register, admin_login, login, logout, logout_admin, change_password, edit_profile
from admin import admin_index, admin_view_project, reset_password, update_last_active, view_pdf, capstone_projects, active_users, users, upload_project, edit_project, delete_capstone_project, delete_user
from flask_session import Session
import uuid as uuid
from config import Config
from flask_cors import CORS


app = Flask(__name__)
# Configure server-side session storage
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config.from_object(Config)
app.jinja_env.filters['basename'] = basename_filter


Session(app)

# Routes from authentication.py
app.add_url_rule('/signup/user', endpoint='register_user', view_func=user_register, methods=['GET', 'POST'])
app.add_url_rule('/signup/admin', endpoint='register_admin', view_func=admin_register, methods=['GET', 'POST'])
app.add_url_rule('/profile_actions/edit_profile', endpoint='edit_profile', view_func=edit_profile, methods=['GET', 'POST'])
app.add_url_rule('/login', endpoint='login', view_func=login, methods=['GET', 'POST'])
app.add_url_rule('/login/admin', endpoint='admin_login', view_func=admin_login, methods=['GET', 'POST'])
app.add_url_rule('/logout', endpoint='logout', view_func=logout, methods=['GET','POST'])
app.add_url_rule('/admin/logout', endpoint='logout_admin', view_func=logout_admin)

# Routes from user.py
app.add_url_rule('/capsarc', endpoint='index', view_func=index)
app.add_url_rule('/home', endpoint='home', view_func=home, methods=['GET'])
app.add_url_rule('/search', endpoint='search', view_func=search)
app.add_url_rule('/user_library', endpoint='user_library', view_func=user_library, methods=['GET'])
app.add_url_rule('/browse', endpoint='browse', view_func=browse, methods=['GET'])
app.add_url_rule('/about', endpoint='about', view_func=about)
app.add_url_rule('/about_us', endpoint='about_us', view_func=about_us)
app.add_url_rule('/reset_password_request', endpoint='reset_password_request', view_func=reset_password_request)
app.add_url_rule('/profile_actions/change_password', endpoint='change_password', view_func=change_password, methods=['GET', 'POST'])
app.add_url_rule('/profile', endpoint='user_profile', view_func=user_profile, methods=['GET', 'POST'])
app.add_url_rule('/project/<identifier>', endpoint='project_details', view_func=project_details)
app.add_url_rule('/save_project', endpoint='save_project', view_func=save_project, methods=['POST'])
app.add_url_rule('/delete_project', endpoint='delete_project', view_func=delete_project, methods=['POST'])


#Routes from admin.py
app.add_url_rule('/admin_dashboard', endpoint='admin_index', view_func=admin_index, methods=['GET'])
app.add_url_rule('/admin/view_project/<int:project_id>', endpoint='admin_view_project', view_func=admin_view_project)
app.add_url_rule('/admin/reset_password/<int:user_id>', endpoint='reset_password', view_func=reset_password,methods=['GET', 'POST'])
app.add_url_rule('/admin/capstone_projects', endpoint='capstone_projects', view_func=capstone_projects, methods=['GET'])
app.add_url_rule('/admin/users', endpoint='users', view_func=users, methods=['GET'])
app.add_url_rule('/admin/active_users', endpoint='active_users', view_func=active_users, methods=['GET'])
app.add_url_rule('/admin/upload_project', endpoint='upload_project', view_func=upload_project, methods=['GET', 'POST'])
app.add_url_rule('/admin/edit_project/<int:project_id>', endpoint='edit_project', view_func=edit_project, methods=['GET', 'POST'])
app.add_url_rule('/admin/delete_project', endpoint='delete_capstone_project', view_func=delete_capstone_project, methods=['POST'])
app.add_url_rule('/admin/delete_user', endpoint='delete_user', view_func=delete_user, methods=['POST'])
app.add_url_rule('/view_pdf/<identifier>', endpoint='view_pdf', view_func=view_pdf)
app.add_url_rule('/update_last_active', endpoint='update_last_active', view_func=update_last_active)
app.before_request




if __name__ == '__main__':
    app.run(debug=True)
CORS(app)