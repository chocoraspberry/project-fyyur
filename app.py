#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from models import Venue, Artist, Show, db
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import collections
collections.Callable = collections.abc.Callable
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  areas = Venue.query.distinct(Venue.state, Venue.city).all() 

  data =[]
  for area in areas:
    venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
    venues_data =[]
    for venue in venues:
      upcoming_shows = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > datetime.today()).all()
      venues_data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(upcoming_shows),
      })
    data.append({
      "city": area.city,
      "state": area.state,
      "venues": venues_data
    })
 
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  items = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  item_data = []
  count = 0
  for item in items:
    upcoming_shows = Show.query.filter_by(venue_id=item.id).filter(Show.start_time > datetime.today()).all()
    item_data.append({
      "id": item.id,
      "name": item.name,
      "num_upcoming_shows":len(upcoming_shows)
    })
    count += 1

  response={
    "count": count,
    "data": item_data
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
  }
  # shows = Show.query.filter_by(venue_id=venue_id).all()
  shows = Show.query.join(Venue, Venue.id == Show.venue_id).filter(Venue.id == venue_id).all()
  past_shows_data = []
  upcoming_shows_data = []
  for show in shows:
    if show.start_time < datetime.today():
      past_shows_data.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artisit_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
      })
    else:
      upcoming_shows_data.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
      })

  

  data["past_shows"] = past_shows_data
  data["upcoming_shows"] = upcoming_shows_data
  data["past_shows_count"] = len(past_shows_data)
  data["upcoming_shows_count"] = len(upcoming_shows_data)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm(meta={'csrf':False})
  if form.validate():
    try:
      venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, 
      address=form.address.data, phone=form.phone.data, genres=form.genres.data, 
      facebook_link=form.facebook_link.data, image_link=form.image_link.data, 
      website=form.website_link.data, seeking_talent=form.seeking_talent.data, 
      seeking_description=form.seeking_description.data)
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + form.name.data + ' was successfully listed!')
    except: 
      db.session.rollback()
      flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    finally: 
      db.session.close()
    
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  
  return render_template('pages/home.html')
  # return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.order_by('id').all()
  data = []
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name,
    })
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  items = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  item_data = []
  count = 0
  for item in items:
    upcoming_shows = Show.query.filter_by(artist_id=item.id).filter(Show.start_time > datetime.today()).all()
    item_data.append({
      "id": item.id,
      "name": item.name,
      "num_upcoming_shows":len(upcoming_shows)
    })
    count += 1

  response={
    "count": count,
    "data": item_data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
  }
  # shows = Show.query.filter_by(artist_id=artist_id).all()
  shows = Show.query.join(Artist, Artist.id == Show.artist_id).filter(Artist.id == artist_id).all()
  past_shows_data = []
  upcoming_shows_data = []
  for show in shows:
    if show.start_time < datetime.today():
      past_shows_data.append({
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
      })
    else:
      upcoming_shows_data.append({
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
      })

  data["past_shows"] = past_shows_data
  data["upcoming_shows"] = upcoming_shows_data
  data["past_shows_count"] = len(past_shows_data)
  data["upcoming_shows_count"] = len(upcoming_shows_data)

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  
  item = Artist.query.get(artist_id)
  
  form = ArtistForm(name=item.name, city=item.city, state=item.state, phone=item.phone, genres=item.genres, 
  website_link=item.website, facebook_link=item.facebook_link, seeking_venue=item.seeking_venue, 
  seeking_description=item.seeking_description, image_link=item.image_link)

  artist = {
    "id": item.id,
    "name": item.name,
    "genres": item.genres,
    "city": item.city,
    "state": item.state,
    "phone": item.phone,
    "website": item.website,
    "facebook_link": item.facebook_link,
    "seeking_venue": item.seeking_venue,
    "seeking_description": item.seeking_description,
    "image_link": item.image_link
}
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(meta={'csrf':False})
  item = Artist.query.get(artist_id)
  if form.validate():
    try:
      item.name = form.name.data
      item.genres = form.genres.data
      item.city = form.city.data
      item.state = form.state.data
      item.phone = form.phone.data
      item.website = form.website_link.data
      item.facebook_link = form.facebook_link.data
      item.seeking_venue = form.seeking_venue.data
      item.seeking_description = form.seeking_description.data
      item.image_link = form.image_link.data
      db.session.commit()
    except:
      db.session.rollback()
    finally:
      db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # TODO: populate form with values from venue with ID <venue_id>
  item = Venue.query.get(venue_id)
  form = VenueForm(name=item.name, city=item.city, state=item.state, address=item.address, phone=item.phone, genres=item.genres, 
  website_link=item.website, facebook_link=item.facebook_link, seeking_talent=item.seeking_talent, 
  seeking_description=item.seeking_description, image_link=item.image_link)

  venue = {
    "id": item.id,
    "name": item.name,
    "genres": item.genres,
    "city": item.city,
    "state": item.state,
    "address": item.address,
    "phone": item.phone,
    "website": item.website,
    "facebook_link": item.facebook_link,
    "seeking_talent": item.seeking_talent,
    "seeking_description": item.seeking_description,
    "image_link": item.image_link
  }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(meta={'csrf':False})
  item = Venue.query.get(venue_id)
  if form.validate():
    try:
      item.name = form.name.data
      item.genres = form.genres.data
      item.city = form.city.data
      item.state = form.state.data
      item.address = form.address.data
      item.phone = form.phone.data
      item.website = form.website_link.data
      item.facebook_link = form.facebook_link.data
      item.seeking_talent = form.seeking_talent.data
      item.seeking_description = form.seeking_description.data
      item.image_link = form.image_link.data
      db.session.commit()
    except:
      db.session.rollback()
    finally:
      db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(meta={'csrf':False})
  if form.validate():
    try:
      artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, 
      phone=form.phone.data, genres=form.genres.data, 
      facebook_link=form.facebook_link.data, image_link=form.image_link.data, 
      website=form.website_link.data, seeking_venue=form.seeking_venue.data, 
      seeking_description=form.seeking_description.data)
      db.session.add(artist)
      db.session.commit()
      flash('Venue ' + form.name.data + ' was successfully listed!')
    except: 
      db.session.rollback()
      flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    finally: 
      db.session.close()

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows = Show.query.all()
  data = []
  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm()
  if form.validate():
    try:
      show = Show(venue_id=form.venue_id.data, artist_id=form.artist_id.data, start_time=form.start_time.data)
      db.session.add(show)
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')
    except:
      # TODO: on unsuccessful db insert, flash an error instead.
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
    finally:
      db.session.close()
 
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

