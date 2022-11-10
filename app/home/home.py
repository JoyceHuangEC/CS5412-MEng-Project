from azure.cosmos import CosmosClient
from multiprocessing import JoinableQueue
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from requests import request

from flask import Flask, redirect, url_for, render_template, Blueprint, session, request

home_bp = Blueprint("home", __name__, static_folder="static",  static_url_path='/static/home', template_folder="templates")

URL = "https://playground2.documents.azure.com:443/"
KEY = "v2V0lRtUsNNYEckQfGlvrAOFGjxhxGkKDSge2CXMccGdKB2lSxXmmfMtyuUcjeWuBCaCTntdeGf0QnFB9C8xuQ=="
client = CosmosClient(URL, credential=KEY)
DATABASE_NAME = 'Job Board'
database = client.get_database_client(DATABASE_NAME)

CONTAINER_NAME = 'Positions'
container = database.get_container_client(CONTAINER_NAME)
CONTAINER_NAME2 = 'Applications'
application_container = database.get_container_client(CONTAINER_NAME2)

@home_bp.route("/", methods = ["POST", "GET"])
def home():
    #init steps
    if not session.get("page"): 
        session["page"] = 0
    if not session.get("data"):
        session["data"] = list(container.query_items(
        query='SELECT * FROM c',
        enable_cross_partition_query=True))

    error = None
    error_job_id = None
    if request.method == "POST":
        #change pages
        if "changePage" in request.form.keys():
            if request.form["changePage"] == "next":
                session["page"] += 1
            elif request.form["changePage"] == "last" and session["page"] > 0:
                session["page"] -= 1
        #print("cur_page is : ",session["page"]+1)
    
        #apply job
        elif "apply" in request.form.keys():
            if (request.form["apply"]):
                job_id = request.form["apply"]
                user_email = current_user.get_username()['email']
                application_info = list(application_container.query_items(
                    query='SELECT * FROM c WHERE c.job_id = @job_id AND c.email = @email', 
                    parameters=[dict(name = "@job_id", value = job_id), dict(name="@email", value=user_email)], 
                    enable_cross_partition_query=True))
                if (len(application_info) == 0):
                    application_container.upsert_item({"email":user_email, 
                        "job_id": job_id, "status": "submitted"})
                    # print(job_id)
                    # print(current_user.get_username()['email'])
                else:
                    error = 'you have already applied for this job'
                    error_job_id = job_id
                    print("application already exist")

    n_results = len(session["data"])
    data = session["data"][session["page"]*5: session["page"]*5+5]
    info = {}
    info["jobs"] = data
    info["page"] = session["page"] + 1
    info["n_results"] = n_results
    return render_template("home.html", info = info, error = error, error_job_id = error_job_id)

@home_bp.route("/job<job_id>")
def position(job_id):
    job_info = list(container.query_items(query=f'SELECT * FROM c WHERE c.job_id = "{job_id}"', enable_cross_partition_query=True))[0]
    return render_template("job_description.html", job_info = job_info)
