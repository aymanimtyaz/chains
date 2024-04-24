# Chains
Chains is a backend web framework written in Python. Chains follows the [WSGI](https://peps.python.org/pep-3333/) specification for web applications and the design of the framework is based on the [chain of responsibility](https://refactoring.guru/design-patterns/chain-of-responsibility) pattern.
Since Chains follows the WSGI spec, it can work with any WSGI based webserver (eg. [Gunicorn](https://gunicorn.org/), [uWSGI](https://uwsgi-docs.readthedocs.io), etc.)
**NOTE: THIS IS A TOY PROJECT AND SHOULD NOT BE USED IN A PRODUCTION SETTING**



## Usage and Dependencies
### Usage
Clone this repository and put it in the working directory of your project to use it.
### Dependencies
Chains does not depend on any other third party libraries as of yet. However, the typing_extensions module might need to be updated for running it with some versions
of Python

## Features

 - WSGI Compliant - Works with any WSGI webserver
 - Support for route functions
 - Support for wildcard routes
 - Support for branches
 - Support for middleware
 
## In The Works
 
 - ~~A dependency injection system for middleware~~
 - A dependency injection system for routes
 - Wildcard branches
 - Functional (without using a decorator) APIs for adding middleware and route functions
 - Validation of parameters such as request method, request path, etc.
 
## An Example Chains Webapp
```py
from chains import Chains, Branch, Request, Response, RequestHandler



# Creating the webapp using Chains, a WSGI compliant web framework
application: Chains = Chains()



users_dictionary: dict[str, str] = dict()



# Creating the index route for the webapp, route functions receive request
# objects and should return response objects
@application.route(path="/", method="GET")
def index(request: Request) -> Response:
    # Response are built in multiple steps, a barebones response must
    # contain at least the status code and the status text, which
    # is what the constructor takes
    response: Response = Response(status_code=200, status_text="OK")
    # The body and headers can be set on the response object using inbuilt
    # setters. Getters and deleters for different parts of the response
    # exist as well.
    response.body = "Welcome to myApplication!!"
    response.headers.set_single_value_header(name="Content-Type", value="text/plain").set_single_value_header(name="Content-Length", value=len(response.body))
    return response



# Branches can be created off of the root webapp and off of other
# branches as well, care must be taken to ensure that path
# clashes don't occur between routes and branches off of a branch.
# The framework will raise an error in that case
user_branch: Branch = Branch()



@user_branch.route("/", method="POST")
def add_user(request: Request) -> Response:
    request_body: str = request.body
    username, fullname = request_body.split(",")
    if username in users_dictionary:
        response: Response = Response(status_code=409, status_text="CONFLICT")
        response.body = "A user with the same username already exists, please choose a different username"
    else:
        users_dictionary[username] = fullname
        response: Response = Response(status_code=201, status_text="CREATED")
        response.body = "The user was created"
    response.headers.set_single_value_header(name="Content-Type", value="text/plain").set_single_value_header(name="Content-Length", value=len(response.body))
    return response



# Wildcard routes can designated by setting '<>' in the path
@user_branch.route("/username/<>", method="GET")
def get_user_by_username(request: Request) -> Response:
    username: str = request.path.split("/")[-1]
    if username not in users_dictionary:
        response: Response = Response(status_code=404, status_text="NOT FOUND")
        response.body = "The specified user does not exist"
    else:
        response: Response = Response(status_code=200, status_text="OK")
        response.body = f"User('{username}', '{users_dictionary[username]}')"
    response.headers.set_single_value_header(name="Content-Type", value="text/plain").set_single_value_header(name="Content-Length", value=len(response.body))
    return response



# The path for the branch is set while attaching it to its parent branch
# the parent branch in this case is the root webapp itself
application.add_branch(path="/user", branch=user_branch)



# Middleware can be added to branches and the root application, the
# middleware functions can intercept the request and response in transit.
# Middleware can be used to make changes to the request using its getter,
# setter, and deleters, the middleware will receive the request and the
# next handler, i.e. the next 'link in the chain' and it should call it
# to send the request downstream, once it receives the response, it can
# make changes to it and return it once done.
# middleware are run sequentially, with the first middleware added being
# run last
# the decorator must always end with '()' otherwise the middleware will
# not be registered
@application.middleware()
def print_request_and_response_middleware(request: Request, next: RequestHandler) -> Response:
    # This is a simple middleware that intercepts every request, prints it
    # sends it downstream to get a response, prints it, and returns it
    print(request)
    # sending the request downstream and getting a response
    response: Response = next(request)
    print(response)
    return response



# middleware functions can also take custom arguments after the request
# and the next handler, keep in mind that these arguments must be
# passed to the decorator as well otherwise they will throw errors
# during runtime when they are to be executed
@application.middleware(req_per_sec: int = 10)
def rate_limiter_middleware(request: Request, next: RequestHandler, req_per_sec: int) -> Response:
    # checks if the request rate limit is exceeded and returns a 429 if so
    if ...: # rate limit check would go here
        response: Response = Response(
            status_code=429,
            status_text="TOO MANY REQUESTS"
        )
        response.headers.set_single_value_header(
            name="Retry-After", value=...
        )
        return response
    else:
        return next(request)
```