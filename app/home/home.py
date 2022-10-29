from multiprocessing import JoinableQueue

from requests import request
from flask import Flask, redirect, url_for, render_template, Blueprint, session, request
from azure.cosmos import CosmosClient

home_bp = Blueprint("home", __name__, static_folder="static",  static_url_path='/static/home', template_folder="templates")

URL = "https://playground2.documents.azure.com:443/"
KEY = "v2V0lRtUsNNYEckQfGlvrAOFGjxhxGkKDSge2CXMccGdKB2lSxXmmfMtyuUcjeWuBCaCTntdeGf0QnFB9C8xuQ=="
client = CosmosClient(URL, credential=KEY)
DATABASE_NAME = 'Job Board'
database = client.get_database_client(DATABASE_NAME)

CONTAINER_NAME = 'Positions'
container = database.get_container_client(CONTAINER_NAME)


@home_bp.route("/", methods = ["POST", "GET"])
def home():
    #init steps
    if not session.get("page"): 
        session["page"] = 0
    if not session.get("data"):
        session["data"] = list(container.query_items(
        query='SELECT * FROM c',
        enable_cross_partition_query=True))

    #change pages
    if request.method == "POST":
        if request.form["changePage"] == "next":
            session["page"] += 1
        elif request.form["changePage"] == "last" and session["page"] > 0:
            session["page"] -= 1
        #print("cur_page is : ",session["page"]+1)

    n_results = len(session["data"])
    data = session["data"][session["page"]*5: session["page"]*5+5]
    info = {}
    info["jobs"] = data
    info["page"] = session["page"] + 1
    info["n_results"] = n_results
    return render_template("home.html", info = info)

@home_bp.route("/job<job_id>")
def position(job_id):
    job_info = list(container.query_items(query=f'SELECT * FROM c WHERE c.job_id = "{job_id}"', enable_cross_partition_query=True))[0]
    return render_template("job_description.html", job_info = job_info)
