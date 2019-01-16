import os
import secrets
from shutil import copyfile
import datetime
from avr import app
import traceback

def delete_image(imageName, folder):
	if imageName is not None:
		imageFolder = os.path.join(app.root_path, 'static', 'images', folder)
		try:
			os.remove(os.path.join(imageFolder, imageName))
		except OSError as e:
			app.logger.error('could not delete image {}, Error is: {}'.format(os.path.join(imageFolder, imageName), e))


def delete_proposed_project_image(imageName):
	delete_image(imageName, "proposed_projects")

def delete_project_image(imageName):
	delete_image(imageName, "projects")

def delete_profile_image(imageName):
	delete_image(imageName, "profile")


def copy_project_image_from_proposed_project(matchingImageName):
	random_hex = secrets.token_hex(8)
	_, matchingExt = os.path.splitext(matchingImageName)
	newImageName = random_hex + matchingExt
	sourcePath = os.path.join(app.root_path, 'static', 'images', 'proposed_projects', matchingImageName)
	destinationFolder = os.path.join(app.root_path, 'static', 'images', 'projects')
	if not os.path.exists(destinationFolder):
		try:
			os.makedirs(destinationFolder)
		except Exception as e:
			app.logger.error('could not make dir {}, Error is: {}\n{}'.format(destinationFolder, e, traceback.format_exc()))
	try:
		copyfile(sourcePath, os.path.join(destinationFolder, newImageName))
		app.logger.info('file {} was copied successfully to {}'.format(sourcePath, os.path.join(destinationFolder, newImageName)))
		return newImageName
	except Exception as e:
		app.logger.error('could not copyfile {}, Error is: {}\n{}'.format(sourcePath, e, traceback.format_exc()))
	

def save_form_image(form_image, folder):
	random_hex = secrets.token_hex(8)
	_, imageExt = os.path.splitext(form_image.filename)
	imageName = random_hex + imageExt
	imageFolder = os.path.join(app.root_path, 'static', 'images', folder)
	
	if not os.path.exists(imageFolder):
		try:
			os.makedirs(imageFolder)
		except Exception as e:
			app.logger.error('could not make dir {}, Error is: {}'.format(imageFolder, e))

	imagePath = os.path.join(imageFolder, imageName)
	# if this file name is already taken, try maximum 20 other random file names
	for i in range(20):
		if not os.path.isfile(imagePath):
			break
		imageName = secrets.token_hex(8) + imageExt
		imagePath = os.path.join(imageFolder, imageName)

	app.logger.info('saving {}'.format(imagePath))
	form_image.save(imagePath)

	return imageName

def getRegistrationSemester():
	currentMonth = int(datetime.datetime.now().strftime("%m"))
	if currentMonth >= 1 and currentMonth <= 6:
		return "Spring"
	else:
		return "Winter"

def getRegistrationYear():
	currentMonth = int(datetime.datetime.now().strftime("%m"))
	currentYear = int(datetime.datetime.now().strftime("%Y"))
	if currentMonth >= 1 and currentMonth <= 6:
		return str(currentYear)
	else:
		return str(currentYear+1)
