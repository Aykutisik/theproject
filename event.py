from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,IntegerField,PasswordField,validators,RadioField,SelectField,BooleanField,DateTimeField
from passlib.hash import sha256_crypt
from functools import wraps


#Registiration form
#Loginrequired decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if "logged_in" in session:

            return f(*args, **kwargs)
        else:
            flash("This page can be seen by the registered users only","danger")
            return redirect(url_for("login"))
    return decorated_function
class PosterForm(Form):
    posterslogan = StringField("Poster Slogan")
    postername = StringField("Poster Name")



class RegisterForm(Form):
    name = StringField("Name Surname",validators=[validators.Length(min = 4,max = 25)])
    username = StringField("Username",validators=[validators.Length(min = 5,max = 35)])
    email = StringField("email",validators=[validators.Email(message = "Please enter a valid email")])
    password = PasswordField("Ppassword: ", validators = [validators.DataRequired(message="Please enter a pass"),validators.EqualTo(fieldname = "confirm",message = "Dont match")])
    gender = RadioField('gender', choices = ['male', 'female'])
    confirm = PasswordField("password correction")
    language = SelectField(u'Programming Language', choices=[('cpp', 'C++'), ('py', 'Python'), ('text', 'Plain Text')])
    agreement = BooleanField("I agree.")
class NewPassword(Form):
    oldpass = PasswordField("Old password")
    newpass = PasswordField("New password")
class LoginForm(Form):
    username = StringField("Username")
    password = PasswordField("Password")

class TicketForm(Form):
    seatletter = SelectField(u'Seat Letter', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'),('D','D'),('E','E'),('F','F'),('G','G')])
    seatnumber = IntegerField('Seat Number', [validators.Length(min=1, max=10, message="TTicket should be 10 digits (no spaces)")])

class SponsorForm(Form):
    sponsorname = StringField("Sponsor Name",validators=[validators.Length(min = 4,max = 25)])
    budget =  IntegerField('Budget')


app = Flask(__name__)
app.secret_key = "eventblog"

app.config["MYSQL_HOST"] = "eu-cdbr-west-03.cleardb.net"
app.config["MYSQL_USER"] = "b42b25c74be6f2"
app.config["MYSQL_PASSWORD"] = "a56bf11a"
app.config["MYSQL_DB"] = "heroku_784288a0ea34592"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route("/")
def index():

    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From events where eventname = %s group by events.title"
 #   sorgu = "Select count(id), title, id from events group by title  "
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0 :
        events = cursor.fetchall()
        return render_template("dashboard.html",events = events)
    else:
        
        return render_template("dashboard.html")


#@app.route("/event/<int:id>")
#def detail(id):
#   return str(id + 5)

#register
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name  = form.name.data 
        username = form.username.data 
        email = form.email.data 
        password = sha256_crypt.encrypt(form.password.data)
        gender = form.gender.data
        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password,gender) VALUES(%s,%s,%s,%s,%s) "
        cursor.execute(sorgu,(name,email,username,password,gender))
        mysql.connection.commit()
        cursor.close()
        flash("Successfully registered","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)

#login
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data


        cursor = mysql.connection.cursor()
        
        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu,(username,))
        if result > 0 :
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
            #if password_entered == real_password:
                flash("Succesfull login","success")

                session["logged_in"] = True
                session["username"] = username
                session["id"] = data["id"]
                return redirect(url_for("index"))
            else:
                flash("Wrong Password","danger")
                return redirect(url_for("login"))
        else:
            flash("This user is not exist","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form=form)






#Delete Event

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()


    sorgu = "Select * from events where eventname = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from events where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("There is no such a event or you have not authorization to delete","danger")
        return redirect(url_for("index"))



#DeleteTicket
@app.route("/deletetic/<string:id>")
@login_required
def deletetic(id):
    cursor = mysql.connection.cursor()


    sorgu = "Select * from eventticket where id = %s"

    result = cursor.execute(sorgu,(id,))
    if result > 0:
        sorgu2 = "Delete from eventticket where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("mytickets"))

    else:
        flash("There is no such a event or you have not authorization to delete","danger")
        return redirect(url_for("index"))


#Event Update
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from events where id = %s and eventname = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0 :
            flash("Böyle bir event yok veya bu işleme etkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            event = cursor.fetchone()
            form = EventForm()

            form.title.data = event["title"]
            form.eventplace.data = event["eventplace"]
            form.starttime.data = event["starttime"]
            form.eventtype.data = event["eventtype"]
            return render_template("update.html",form = form)

    else:
        #POST REQUEST
        form = EventForm(request.form)
        newtitle = form.title.data 
        neweventplace = form.eventplace.data  
        newstarttime = form.starttime.data
        neweventtype = form.eventtype.data
        sorgu2 = "Update events Set title = %s, eventplace = %s, starttime = %s, eventtype = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newtitle,neweventplace,newstarttime,neweventtype,id))
        mysql.connection.commit()
        flash("Event is successfully updated","success")
        return redirect(url_for("dashboard"))


@app.route("/updatetic/<string:id>",methods = ["GET","POST"])
@login_required
def updateticket(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from eventticket where id = %s"
        result = cursor.execute(sorgu,(id,))

        if result == 0 :
            flash("Böyle bir eventticket yok veya bu işleme etkiniz yok","danger")
            return redirect(url_for("mytickets"))
        else:
            eventticket = cursor.fetchone()
            form = TicketForm()

            form.seatletter.data = eventticket["seatletter"]
            form.seatnumber.data = eventticket["seatnumber"]
            #form.eventplace.data = event["eventplace"]
            #form.starttime.data = event["starttime"]
            return render_template("updateticket.html",form = form)
    else:
        form = TicketForm(request.form)
        newseatletter = form.seatletter.data 
        newseatnumber = form.seatnumber.data  
        
        sorgu2 = "Update eventticket Set seatletter = %s, seatnumber = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newseatletter,newseatnumber,id))
        mysql.connection.commit()
        flash("Event is successfully updated","success")
        return redirect(url_for("mytickets"))









#Detail event
@app.route("/event/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from events where id = %s "

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        event = cursor.fetchone()
        return render_template("event.html",event = event)
        
    else:
        return render_template("event.html")









#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/deleteaccount")
@login_required
def deleteaccount():
    cursor = mysql.connection.cursor()

    sorgu = "Select * from users where username = %s"

    #sorgu = "Select * From events"

    result = cursor.execute(sorgu,(session["username"],))
    a = cursor.fetchone()
    
    if result > 0:
        sorgu2 = "Delete from users where id = %s"
        cursor.execute(sorgu2,(a["id"],))
        mysql.connection.commit()
        session.clear()
        return redirect(url_for("login"))
    else:
        flash("Your account can not deleted","danger")
        return redirect(url_for("profile"))


#eventpage
@app.route("/events")
def events():
    cursor = mysql.connection.cursor()

    sorgu = "Select count(id), title,id from events group by title"
    #sorgu = "Select * From events"

    result = cursor.execute(sorgu)

    if result > 0:
        events = cursor.fetchall()
        return render_template("events.html",events = events)
    else:
        return render_template("events.html")

#addingevent
@app.route("/addevent",methods = ["GET","POST"])
def addevent():
    form  = EventForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        eventplace = form.eventplace.data 
        starttime = form.starttime.data
        eventtype = form.eventtype.data 
        cursor = mysql.connection.cursor()

        sorgu = "Insert into events(title,eventname,eventplace,starttime,eventtype) VALUES(%s,%s,%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],eventplace,starttime,eventtype))
        mysql.connection.commit()
        cursor.close()
        flash("Event is successfully added","success")
        return redirect(url_for("dashboard"))
    return render_template("addevent.html",form = form) 

@app.route("/addsponsor",methods = ["GET","POST"])
def addsponsor():
    form = SponsorForm(request.form)
    if request.method == "POST" and form.validate():
        sponsorname = form.sponsorname.data
        budget = form.budget.data   
        cursor = mysql.connection.cursor()

        sorgu = "Insert into sponsors(sponsorname,budget) VALUES(%s,%s)"
        cursor.execute(sorgu,(sponsorname,budget))
        mysql.connection.commit()
        cursor.close()
        flash("Sponsor is successfully added","success")
        return redirect(url_for("sponsors"))
    return render_template("addsponsor.html",form = form)
#Search 
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()

        sorgu = "Select * from events where title like '%" + keyword + "%' "

        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan kelimeye uygun kelime bulunamadı","warning")
            return render_template(url_for("events"))
        else:
            events = cursor.fetchall()
            return render_template("events.html",events = events)


@app.route("/sponsor/<string:sponsorid>/<string:eventid>")
@login_required
def sponsorevent(sponsorid,eventid):

        sorgu = "Update events Set sponsorid = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu,(sponsorid,eventid))
        mysql.connection.commit()
        flash("Sponsor is successfully updated","success")
        return redirect(url_for("sponsors"))


    



@app.route("/mytickets")
@login_required
def mytickets():
    cursor = mysql.connection.cursor()

    #sorgu2 = "Select * from eventticket where eventname = %s"
    sorgu = "Select username from users join eventticket on eventticket.ownerid = %s"

    result1 = cursor.execute(sorgu,(session["id"],))
    theusername = cursor.fetchone()
    #result = cursor.execute(sorgu,(session["username"],))
    sorgu2 = "Select * from eventticket where eventname = %s"
    result = cursor.execute(sorgu2,(session["username"],))
    if result == 0:
        flash("Hiç biletiniz yok","warning")
        return render_template("mytickets.html")
    else:
        tickets = cursor.fetchall()
        return render_template("mytickets.html",tickets = tickets)

@app.route("/addposter",methods = ["GET","POST"])
@login_required
def addposters():
    form  = PosterForm(request.form)
    if request.method == "POST" and form.validate():
        slogan = form.posterslogan.data
        postername = form.postername.data 
        
        cursor = mysql.connection.cursor()

        sorgu = "Insert into posters(slogan,postername) VALUES(%s,%s)"
        cursor.execute(sorgu,(slogan,postername))
        mysql.connection.commit()
        cursor.close()
        flash("Event is successfully added","success")
        return redirect(url_for("posters"))
    return render_template("addposter.html",form = form) 


@app.route("/posters")
@login_required
def posters():
    cursor = mysql.connection.cursor()



    sorgu = "Select * from posters"
    result = cursor.execute(sorgu)
    if result > 0 :
        
        posters = cursor.fetchall()
        return render_template("poster.html",posters = posters)
    return render_template("poster.html")

#addticket 
@app.route("/addticket/<string:id>")
@login_required
def addticket(id):
    cursor = mysql.connection.cursor()



    sorgu = "Select * from events where id = %s"
    result = cursor.execute(sorgu,(id,))
    event = cursor.fetchone()
    _eventname = event["eventname"]
    _starttime = event["starttime"]
    _title = event["title"]
    sorgu2 = "Select * from users where username = %s"
    result = cursor.execute(sorgu2,(session["username"],))
    userm = cursor.fetchone()
    user_id = userm["id"]


    sorgu = "Insert into eventticket(eventname,starttime,eventid,ownerid,eventname2) VALUES(%s,%s,%s,%s,%s)"
    cursor.execute(sorgu,(session["username"],_starttime,id,user_id,_title))
    mysql.connection.commit()
    cursor.close()    

    return redirect(url_for("mytickets"))



@app.route("/profile",methods = ["GET","POST"])
@login_required
def profile():
    form = NewPassword(request.form)
    if request.method == "POST":
        oldpass = form.oldpass.data
        newpass = sha256_crypt.encrypt(form.newpass.data)


        cursor = mysql.connection.cursor()
        
        sorgu = "Select * from users where username = %s"

        result = cursor.execute(sorgu,(session["username"],))
        if result > 0 :
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(oldpass,real_password):
            #if oldpass == real_password:
                flash("Password is changed","success")
                sorgu2 = "Update users Set password = %s where username = %s"
                cursor.execute(sorgu2,(newpass,session["username"]))
                mysql.connection.commit()
                #session["id"] = id
                return redirect(url_for("profile"))
            else:
                flash("Wrong Password","danger")
                return redirect(url_for("profile"))
        else:
            flash("This user is not exist","danger")
            return redirect(url_for("profile"))

    return render_template("profile.html",form=form)









@app.route("/sponsors")
@login_required
def sponsors():
    cursor = mysql.connection.cursor()

    sorgu = "Select count(id_), sponsorname,id_,budget from sponsors group by budget"
    #sorgu = "Select * From events"

    result = cursor.execute(sorgu)
    sorgu2 = "Select events.title, events.id, sponsors.id_,events.sponsorid from events inner join sponsors on events.sponsorid != sponsors.id_"
    if result > 0:
        sponsors = cursor.fetchall()
        cursor.execute(sorgu2)
        theevents = cursor.fetchall()
        return render_template("sponsors.html",sponsors = sponsors,theevents=theevents)
    else:
        
        return render_template("sponsors.html")



#EventForm
class EventForm(Form):
    title = StringField("Event Title",validators=[validators.Length(min = 5,max =100)])
    eventplace = TextAreaField("Eventplace",validators=[validators.Length(min = 5,max =100)])
    starttime = StringField('Time of the event DD:HH:MM')
    eventtype = SelectField(u'Eventtype', choices=[('Sport', 'Sport'), ('Education', 'Education'), ('Art', 'Art'),('Technology','Techonology')])

if __name__ == "__main__":
    app.run()


