from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ENUM
import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://udsa:P@ssword2021@92.242.58.173:1984/db_dsa'
db = SQLAlchemy(app)

user_projects = db.Table('user_projects_api',
                         db.Column('user_id', db.BigInteger, db.ForeignKey('users_api.id'), primary_key=True),
                         db.Column('project_id', db.BigInteger, db.ForeignKey('projects_api.id'), primary_key=True))


class Projects_api(db.Model):
    query: db.Query
    id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    name = db.Column(db.String(300), nullable=False)
    goal = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    number_of_students = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.Date)
    team_choice_deadline = db.Column(db.Date)
    status = db.Column(ENUM('finding team',
                            'working on the project',
                            'project finished',
                            name='proj_state'), nullable=False, default='finding team')
    users = db.relationship('Users_api', secondary=user_projects,
                            back_populates="projects")

    def to_dict(self):
        return {"id": self.id,
                "name": self.name,
                "goal": self.goal,
                "description": self.description,
                "number_of_students": self.number_of_students,
                "deadline": self.deadline.strftime('%d.%m.%Y'),
                "team_choice_deadline": self.team_choice_deadline.strftime('%d.%m.%Y'),
                "status": self.status,
                "members": [u.id for u in self.users]
                }


class Users_api(db.Model):
    query: db.Query
    id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    interests = db.Column(db.Text, nullable=False)
    projects = db.relationship('Projects_api', secondary=user_projects,
                               back_populates="users")

    def to_dict(self):
        return {"id": self.id,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "email": self.email,
                "interests": self.interests,
                "projects": [p.id for p in self.projects]
                }


@app.route('/api/users/')
def get_users():
    if 'proj_id' in request.args.keys():
        try:  # checking if the argument is an integer
            tmp = int(request.args["proj_id"])
        except:
            return {"error": "proj_id must be an integer"}
        project = Projects_api.query.get(request.args["proj_id"])  # type:Projects_api
        if project is None:
            return {"error": "Project not found"}
        return {"users": [u.to_dict() for u in project.users]}
    return {"users": [u.to_dict() for u in Users_api.query.all()]}


@app.route('/api/users/<user_id>')
def get_user(user_id):
    user = Users_api.query.get(user_id)  # type:Users_api
    if user is None:
        return {"error": "User not found"}
    return user.to_dict()


# creates a new user with the data in request's body
@app.route('/api/users/', methods=['POST'])
def create_user():
    user = Users_api()
    user.first_name = request.json['first_name']
    user.last_name = request.json['last_name']
    user.email = request.json['email']
    user.interests = request.json['interests']
    db.session.add(user)
    db.session.commit()
    return user.to_dict()


# deletes a user
@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = Users_api.query.get(user_id)
    if user is None:
        return {"error": "User not found"}
    db.session.delete(user)
    db.session.commit()
    return {"message": "User deleted!"}


@app.route('/api/projects/')
def get_projects():
    if 'user_id' in request.args.keys():
        try:  # checking if the argument is an integer
            tmp = int(request.args["user_id"])
        except:
            return {"error": "user_id must be an integer"}
        user = Users_api.query.get(request.args["user_id"])  # type:Users_api
        if user is None:
            return {"error": "User not found"}
        return {"projects": [u.to_dict() for u in user.projects]}
    return {"projects": [u.to_dict() for u in Projects_api.query.all()]}


# returns the project with the <proj_id> id
@app.route('/api/projects/<proj_id>')
def get_project(proj_id):
    project = Projects_api.query.get(proj_id)  # type:Projects_api
    if project is None:
        return {"error": "Project not found"}
    return project.to_dict()


# creates a new project
@app.route('/api/projects/', methods=['POST'])
def create_project():
    project = Projects_api()
    project.name = request.json['name']
    project.goal = request.json['goal']
    project.description = request.json['description']
    project.number_of_students = request.json['number_of_students']
    project.deadline = datetime.datetime.strptime(request.json['deadline'], '%d.%m.%Y')
    project.team_choice_deadline = datetime.datetime.strptime(request.json['team_choice_deadline'], '%d.%m.%Y')
    if 'proj_state' in request.json.keys():
        project.proj_state = request.json['proj_state']
    db.session.add(project)
    db.session.commit()
    return project.to_dict()


@app.route('/api/projects/<proj_id>', methods=['DELETE'])
def delete_project(proj_id):
    project = Projects_api.query.get(proj_id)
    if project is None:
        return {"error": "Project not found"}
    db.session.delete(project)
    db.session.commit()
    return {"message": "Project deleted!"}


@app.route('/api/link-user-project/', methods=['POST'])
def link_user_project():
    proj_id = request.json['proj_id']
    user_id = request.json['user_id']
    user = Users_api.query.get(user_id)  # type:Users_api
    project = Projects_api.query.get(proj_id)  # type:Projects_api
    user.projects.append(project)
    db.session.commit()
    return {"message": "Linked!"}


@app.route('/')
def default_page():
    return "Welcome!"


if __name__ == '__main__':
    app.run()
