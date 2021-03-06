
#!/usr/bin/python3
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import paho.mqtt.publish as publish

PHOTO_ROOT = "./images/"

app = Flask(__name__)

CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://iot:jorenjamar@localhost/IOT'
db = SQLAlchemy(app)

class Foto(db.Model):
	__tablename__ = 'Foto'
	id = db.Column('id', db.Integer, primary_key = True)
	naam = db.Column('naam', db.Unicode)
	lesid = db.Column('lesid', db.Integer, db.ForeignKey('Les.id'))
	les = db.relationship('Les', back_populates='fotos')
	cameraid = db.Column('cameraid', db.Integer, db.ForeignKey('Camera.id'))
	camera = db.relationship('Camera', back_populates = 'fotos')

	def toDict(self, skipLes = False, skipCamera = False):
		ret = {}
		ret['id'] = self.id
		ret['naam'] = self.naam
		if (skipLes == False):
			ret['les'] = self.les.toDict()
		else:
			ret['lesid'] = self.lesid
		if (skipCamera == False):
			ret['camera'] = self.camera.toDict()
		else:
			ret['cameraid'] = self.cameraid
		return ret

class Les(db.Model):
	__tablename__ = 'Les'
	id = db.Column('id', db.Integer, primary_key = True)
	lokaalid = db.Column('lokaalid', db.Integer, db.ForeignKey('Lokaal.id'))
	vakid = db.Column('vakid', db.Integer, db.ForeignKey('Vak.id'))
	klasid = db.Column('klasid', db.Integer, db.ForeignKey('Klas.id'))
	starttijd = db.Column('starttijd', db.DateTime)
	eindtijd = db.Column('eindtijd', db.DateTime)
	fotos = db.relationship('Foto', back_populates='les', lazy='joined')
	vak = db.relationship('Vak', back_populates='lessen')
	klas = db.relationship('Klas', back_populates='lessen')
	lokaal = db.relationship('Lokaal', back_populates='lessen')

	def toDict(self, skipLokaal = False, skipVak = False, skipKlas = False):
		ret = {}
		ret['id'] = self.id
		if (skipLokaal == False):
			ret['lokaal'] = self.lokaal.toDict()
		else:
			ret['lokaalid'] = self.lokaalid
		if (skipVak == False):
			ret['vak'] = self.vak.toDict()
		else:
			ret['vakid'] = self.vakid
		if (skipKlas == False):
			ret['klas'] = self.klas.toDict()
		else:
			ret['klasid'] = self.klasid
		ret['starttijd'] = self.starttijd
		ret['eindtijd'] = self.eindtijd
		return ret

class Klas(db.Model):
	__tablename__ = 'Klas'
	id = db.Column('id', db.Integer, primary_key = True)
	richtingid = db.Column('richtingid', db.Integer, db.ForeignKey('Richting.id'))
	naam = db.Column('naam', db.Integer)
	lessen = db.relationship('Les', back_populates='klas', lazy="joined")
	richting = db.relationship('Richting', back_populates='klassen')

	def toDict(self, skipRichting = False):
		ret = {}
		ret['id'] = self.id
		ret['naam'] = self.naam
		if (skipRichting == False):
			ret['richting'] = self.richting.toDict()
		else:
			ret['richtingid'] = self.richtingid
		return ret

class Lokaal(db.Model):
	__tablename__ = 'Lokaal'
	id = db.Column('id', db.Integer, primary_key = True)
	naam = db.Column('naam', db.Unicode)
	gebouw = db.Column('gebouw', db.Unicode)
	lessen = db.relationship('Les', back_populates='lokaal', lazy='joined')
	cameras = db.relationship('Camera', back_populates='lokaal', lazy='joined')

	def toDict(self):
		ret = {}
		ret['id'] = self.id
		ret['naam'] = self.naam
		ret['gebouw'] = self.gebouw
		return ret

class Prof(db.Model):
	__tablename__ = 'Prof'
	id = db.Column('id', db.Integer, primary_key = True)
	naam = db.Column('naam', db.Unicode)
	vakken = db.relationship('Vak', back_populates='prof', lazy = 'joined')

	def toDict(self):
		ret = {}
		ret['id'] = self.id
		ret['naam'] = self.naam
		return ret

class Richting(db.Model):
	__tablename__ = 'Richting'
	id = db.Column('id', db.Integer, primary_key = True)
	naam = db.Column('naam', db.Unicode)
	klassen = db.relationship('Klas', back_populates='richting', lazy = 'joined')

	def toDict(self):
		ret = {}
		ret['id'] = self.id
		ret['naam'] = self.naam
		return ret

class Vak(db.Model):
	__tablename__ = 'Vak'
	id = db.Column('id', db.Integer, primary_key = True)
	profid = db.Column('profid', db.Integer, db.ForeignKey('Prof.id'))
	naam = db.Column('naam', db.Unicode)
	lessen = db.relationship('Les', back_populates='vak', lazy='joined')
	prof = db.relationship('Prof', back_populates = 'vakken')

	def toDict(self, skipProf = False):
		ret = {}
		ret['id'] = self.id
		ret['naam'] = self.naam
		if (skipProf == False):
			ret['prof'] = self.prof.toDict()
		else:
			ret['profid'] = self.profid
		return ret

class Camera(db.Model):
	__tablename__ = 'Camera'
	id = db.Column('id', db.Integer, primary_key=True)
	lokaalid = db.Column('lokaalid', db.Integer, db.ForeignKey('Lokaal.id'), nullable=True)
	ip = db.Column('ip', db.Unicode, nullable = True)
	lokaal = db.relationship('Lokaal', back_populates = 'cameras')
	fotos = db.relationship('Foto', back_populates = 'camera', lazy='joined')
	enabled = db.Column('enabled', db.Boolean)

	def toDict(self, skipLokaal = False):
		ret = {}
		ret['id'] = self.id
		if (skipLokaal == False):
			if (self.lokaal):
				ret['lokaal'] = self.lokaal.toDict()
		else:
			ret['lokaalid'] = self.lokaalid
		ret['ip'] = self.ip
		ret['enabled'] = self.enabled
		return ret

@app.route('/test')
def test():
	fotos = Foto.query.all()
	lessen = Les.query.all()
	klassen = Klas.query.all()
	lokalen = Lokaal.query.all()
	proffen = Prof.query.all()
	richtingen = Richting.query.all()
	vakken = Vak.query.all()

	test = db.session.query(Foto, Les).filter(Foto.lesid == Les.id).all()

	output = []

	for foto in fotos:
		output.append(foto.toDict())

	return jsonify({'fotos' : output})

@app.route('/photo', methods=['GET'])
def get_all_photosInfo():
	fotos = Foto.query.all()

	output = []

	for foto in fotos:
		output.append(foto.toDict())

	return jsonify({'fotos' : output})

@app.route('/photo/<photo_id>', methods=['GET'])
def get_photoInfo(photo_id):
	foto = Foto.query.filter_by(id = photo_id).first()

	if not foto:
		return jsonify({'message' : 'no photo found'})

	output = foto.toDict()

	return jsonify({'examples' : output})

@app.route('/photo', methods=['POST'])
def create_photo():
	print("create photo")

	# get picture from request
	print(request.files)
	if not ('file' in request.files):	# incorrect naming
		# return error
		print("file not in files")
		resp = jsonify({'error': 'no file found'})
		resp.status_code = 400
		return resp
	file = request.files['file']

	filename = secure_filename(file.filename)
	id = request.values['id']
	id = secure_filename(id)		# id should be a number, but just to be sure
	folder = PHOTO_ROOT + id
	if not os.path.isdir(folder):		# if folder doesn't exist, make new
		os.mkdir(PHOTO_ROOT + id)

	# save picture
	file.save(PHOTO_ROOT + id + '/' + filename)

	if not (Camera.query.filter_by(id = id).all()):
		camera = Camera()
		camera.id = id
		camera.lokaalid = 1
		camera.ip = request.remote_addr
		db.session.add(camera)

	#insert info into DB
	foto = Foto()
	foto.naam = filename
	foto.cameraid = id
	foto.lesid = 1
	db.session.add(foto)
	db.session.commit()
	# return confirmation
	return jsonify({'message': 'New photo added!'})

@app.route('/photo/<photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
	foto = Foto.query.filter_by(id = photo_id).first()

	if not foto:
		return jsonify({'message' : 'no photo found'})

	directory =  PHOTO_ROOT + str(foto.cameraid) + "/" + foto.naam

	if os.path.exists(directory):
		os.remove(directory)
	else:
		return jsonify({'message' : 'no photo path found'})

	db.session.delete(foto)
	db.session.commit()

	return jsonify({'message' : 'foto deleted'})

@app.route('/photo/getphoto/<camera_id>/<photo_naam>', methods=['GET'])
def get_image(camera_id, photo_naam):
	directory = PHOTO_ROOT + camera_id + "/" + photo_naam
	return send_file(directory)

@app.route('/photo/downloadphoto/<camera_id>/<photo_naam>', methods=['GET'])
def get_image_download(camera_id, photo_naam):
        directory = PHOTO_ROOT + camera_id + "/"
        return send_from_directory(directory, photo_naam, as_attachment=True)

@app.route('/takephoto/', methods=['POST'])
def take_photo():
	print(str(request))
	studnr = None
	if (request.is_json):
		studnr = request.json['studnr']
	else:
		studnr = request.values['studnr']

	if studnr is None:
		resp = jsonify({'error': 'no student number'})
		resp.status_code = 400
		return resp
	else:
		# get current classroom of student number
		# dummy:
                if (studnr == "s091234"):
			LokaalId = 1
		else if (studnr == "s099876"):
			LokaalId = 2
		else:
			LokaalId = studnr

		# TODO:
		# get camera at classroom
		# dummy:
		Camera = Camera.query.filter_by(lokaalid = LokaalId).first()

		# send command to camera
		if(camera.enabled):
			publish.single(str(CameraId), b'photo', hostname = "localhost")
			return jsonify({'reply': 'request sent'})
		else:
			resp = jsonify({'error': 'Disabled'})
			resp.status_code = 200
			return 

@app.route('/disablephoto/<camera_id>', methods=['POST'])
def disable_photo(camera_id):
	camera = Camera.query.filter_by(id = camera_id).first()
	camera.enabled = not camera.enabled
	db.session.add(camera)
	db.session.commit()
	return jsonify ({'message': 'camera toggled',
	    'enabled': camera.enabled})


@app.route('/camera/<camera_id>/enabled', methods=['GET'])
def status_camera(camera_id):
	camera = Camera.query.filter_by(id = camera_id).first()

	if not camera:
		return jsonify({'message' : 'no camera found'})

	output = camera.enabled

	return jsonify({'enabled' : output})

@app.route('/init', methods=['GET'])
def get_init():
	config = {}
	camera = Camera()
	camera.enabled = True
	db.session.add(camera)
	db.session.commit()

	config["id"] = camera.id
	config["ssid"] = "bbswifi"
	config["psk"] = "blackboard"
	config["cert"] = "testcert"
	config["mqttbroker"] = "brabo2.ddns.net"
	config["brokerport"] = 1883
	return jsonify(config)

@app.route('/klas', methods=['GET'])
def getKlassen():
	klassen = Klas.query.all()

	output = []

	for klas in klassen:
		output.append(klas.toDict())

	return jsonify({'klassen' : output})

@app.route('/prof', methods=['GET'])
def getProffen():
        proffen = Prof.query.all()

        output = []

        for prof in proffen:
                output.append(prof.toDict())

        return jsonify({'proffen' : output})

@app.route('/vak', methods=['GET'])
def getVakken():
        vakken = Vak.query.all()

        output = []

        for vak in vakken:
                output.append(vak.toDict())

        return jsonify({'vakken' : output})

@app.route('/lokaal', methods=['GET'])
def getLokalen():
        lokalen = Lokaal.query.all()

        output = []

        for lokaal in lokalen:
                output.append(lokaal.toDict())

        return jsonify({'lokalen' : output})

@app.route('/camera', methods=['GET'])
def getCameras():
	cameras = Camera.query.all()
	print(cameras)
	output = []

	for camera in cameras:
		print(camera.toDict())
		output.append(camera.toDict())


	return jsonify({'cameras' : output})

@app.route('/couple', methods=['POST'])
def coupleCamera():
	if (not request.is_json):
		resp = jsonify({'error': 'expected json'})
		resp.status_code = 400
		return resp
	else:
		cameraId = request.json['cameraId']
		lokaalId = request.json['lokaalId']
		camera = Camera.query.filter_by(id = cameraId).first()
		camera.lokaalid = lokaalId
		db.session.commit()
		return jsonify(camera.toDict())

@app.route('/camera/unassigned', methods=['GET'])
def getUnassignedCameras():
	cameras = Camera.query.filter_by(lokaalid = None)
	output = []
	for camera in cameras:
		output.append(camera.toDict())
	return jsonify(output)

if __name__ == '__main__':
	app.run(host='0.0.0.0')

# tutorial die kan bekeken worden: https://www.youtube.com/watch?v=WxGBoY5iNXY
# sqlalchemy tutorial: https://www.youtube.com/watch?v=Tu4vRU4lt6k
