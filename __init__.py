from flask import Flask, render_template, url_for, flash, redirect
from flask_socketio import SocketIO, emit
from form import SearchForm, LoginForm
from get_gameData_from_gamelist import *
import asyncio

loop = asyncio.get_event_loop()
app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'you-will-never-guess'

@app.route("/")
@app.route("/home", methods = ['GET,' 'POST'])
def home():
    form  = SearchForm()
    if form.validate_on_submit():
        flash('Searchdata requested for searchdata {}'.format(
            form.searchdata.data))
        return redirect('/test')
    return render_template('home.html', form = form)

@socketio.on('my event')  
@app.route("/test", methods = ['GET', 'POST'])
def test():
    form = SearchForm()
    if form.validate_on_submit():
        summoner_name = form.searchdata.data
        emit(get_gameData_from_summoner(summoner_name))
        return redirect('/')
    return render_template('test.html', form = form)

@app.route("/summoner", methods = ['GET', 'POST'])
def summoner():
    return render_template('summoner.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)