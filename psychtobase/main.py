import json
import logging
import shutil
import threading
import time

from base64 import b64decode
from pathlib import Path
from PIL import Image

from src import Constants, FileContents, files, log, Utils, window

from src.tools import StageLuaParse, StageTool, VocalSplit, WeekTools
from src.tools import ModConvertTools as ModTools

from src.tools.CharacterTools import CharacterObject
from src.tools.ChartTools import ChartObject 

if __name__ == '__main__':
    log.setup()
    window.init()

# Main

charts = []
characterMap = {
    # 'charactr': 'Name In English'
}
vocalSplitMasterToggle = True

def folderMake(folder_path:str):
    """
    Creates a folder with the path provided.

    Args:
        folder_path (str): Path to create the folder.
    """
    if not Path(folder_path).exists():
        try:
            Path(folder_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error(f'Something went wrong: {e}')
    else:
        logging.warn(f'{folder_path} already exists!')

def fileCopy(source, destination):
    """
    Copies a file to a destination
    
    Args:
        source (str): Path to the file.
        destination (str): Path to where the file should go.
    """
    if Path(source).exists():
        try:
            shutil.copyfile(source, destination)
        except Exception as e:
            logging.error(f'Something went wrong: {e}')
    else:
        logging.warn(f'Path {source} doesn\'t exist.')

def treeCopy(source, destination):
    """
    Copies a folder to a destination
    
    Args:
        source (str): Path to the folder.
        destination (str): Path to where the folder should go.
    """
    if not Path(destination).exists() and Path(source).exists():
        try:
            shutil.copytree(source, destination)
        except Exception as e:
            logging.error(f'Something went wrong: {e}')
    elif not Path(source).exists():
        logging.warn(f'Path {source} does not exist.')

def convert(psych_mod_folder, result_folder, options):
    """
    Converts a mod.
    
    Args:
        psych_mod_folder (str): Path to the Psych Engine mod folder.
        result_folder (str): Path to the Base Game 'mods' folder.
        options (dict): Set of options chosen by the user.
    """

    # Logs the time at which the conversion began.
    runtime = time.time()

    # Announces a large string of text indicating the conversion has began.
    logging.info(Utils.coolText("NEW CONVERSION STARTED"))
    logging.info(options)

    # Variable used to refer to the mod folder path.
    modName = psych_mod_folder

    # Variable used to refer to the name of the mod folder.
    modFoldername = Path(psych_mod_folder).name

    logging.info(f'Converting from{psych_mod_folder} to {result_folder}')

    # Accesses the options to see if the user selected modpack metadata
    if options.get('modpack_meta', False):
        logging.info('Converting pack.json')

        # Accesses the paths of the pack.json file
        dir = Constants.FILE_LOCS.get('PACKJSON')
        psychPackJson = dir[0]
        polymodMetaDir = dir[1]
        
        # Checks if the pack.json file exists
        if Path(f'{modName}{psychPackJson}').exists():

            # Try except to avoid errors
            try:

                # Reads the file and converts it to a valid _polymod_meta.json file
                polymod_meta = ModTools.convertPack(json.loads(open(f'{modName}{psychPackJson}', 'r').read()))

                # Makes sure the folder to which the file will be written to is valid
                folderMake(f'{result_folder}/{modFoldername}/')

                # Writes the file to the path
                open(f'{result_folder}/{modFoldername}/{polymodMetaDir}', 'w').write(json.dumps(polymod_meta, indent=4))
            except Exception as e:
                logging.error('Couldn\'t convert pack.json file')

            logging.info('pack.json converted and saved')
        else:
            # If the file does not exist, write a default one as it is necessary

            # Makes sure the folder to which the file will be written to is valid
            folderMake(f'{result_folder}/{modFoldername}/')

            # Writes a default file to the path
            open(f'{result_folder}/{modFoldername}/{polymodMetaDir}', 'w').write(json.dumps(ModTools.defaultPolymodMeta(), indent=4))
            logging.warn('pack.json not found. Replaced it with default')

        logging.info('Copying pack.png')

        # Accesses the paths to the pack.png file
        dir = Constants.FILE_LOCS.get('PACKPNG')
        psychPackPng = dir[0]
        polymodIcon = dir[1]
        
        # Checks if the path to it exists
        if Path(f'{modName}{psychPackPng}').exists():

            # Makes sure the folder to which the file will be written to is valid
            folderMake(f'{result_folder}/{modFoldername}/')

            # Try except to avoid any errors
            try:
                # Copy the png file to the path
                fileCopy(f'{modName}{psychPackPng}', f'{result_folder}/{modFoldername}/{polymodIcon}')
            except Exception as e:
                logging.error(f'Could not copy pack.png file: {e}')
        else:
            # If the file does not exist, replace it with a default one
            logging.warn('pack.png not found. Replacing it with default')
            try:
                # Generate the path to write it to
                polymodIconpath = f'{result_folder}/{modFoldername}/{polymodIcon}'
                with open(polymodIconpath, 'wb') as output_file:
                    # Write the default png file
                    output_file.write(b64decode(Constants.BASE64_IMAGES.get('missingModImage')))
            except Exception as e:
                logging.error(f'Could not write default file: {e}')

        logging.info('Parsing and converting credits.txt')

        # Accesses the path to the credits.txt
        dir = Constants.FILE_LOCS.get('CREDITSTXT')

        psychCredits = dir[0]
        modCredits = dir[1]

        # Makes sure the path to it exists
        if Path(f'{modName}{psychCredits}').exists():
            # Ensures the folder is valid
            folderMake(f'{result_folder}/{modFoldername}/')

            # Parses the file by opening it
            resultCredits = ModTools.convertCredits(open(f'{modName}{psychCredits}', 'r').read())

            # Writes the text content to a new file
            open(f'{result_folder}/{modFoldername}/{modCredits}', 'w').write(resultCredits)
        else:
            logging.warn(f'Could not find {modName}{psychCredits}')

    # Accesses the chart options selected by the user
    chartOptions = options.get('charts', {
        'songs': False,
        'events':False
    })
    if chartOptions['songs']:

        # Gets the path to the charts folder
        chartFolder = Constants.FILE_LOCS.get('CHARTFOLDER')
        psychChartFolder = modName + chartFolder[0]

        # Ensures the new chart folder exists
        folderMake(f'{result_folder}/{modFoldername}{chartFolder[1]}')

        # Finds all the chart directories
        songs = files.findAll(f'{psychChartFolder}*')

        # Iterates through them
        for song in songs:

            # Checks if they are valid directories
            if Path(song).is_dir():
                logging.info(f'Loading charts in {song}')

                outputpath = f'{result_folder}/{modFoldername}'

                # Opens a new ChartObject instance with the chart's path, output path, and if it should convert events.
                # Try except to avoid any crash
                try:
                    songChart = ChartObject(song, outputpath, chartOptions['events'])
                except FileNotFoundError:
                    # If the charts arent found, this error will be thrown.
                    logging.warning(f"{song} data not found! Skipping...")
                    continue
                except Exception as e:
                    # If any other Exception is found, throw a error
                    logging.error("Error creating ChartObject instance: " + str(e))
                    continue
                else:
                    logging.info(f'{song} successfully initialized! Converting')

                # Converts the chart inside the chart instance
                songChart.convert()

                # Appens the chart to the charts map, to later be used by vocal split
                # Try except to avoid any crash
                try:
                    charts.append({
                        'songKey': songChart.songFile,
                        'sections': songChart.sections,
                        'bpm': songChart.startingBpm,
                        'player': songChart.metadata['playData']['characters']['player'],
                        'opponent': songChart.metadata['playData']['characters']['opponent']
                    })
                except Exception as e:
                    logging.error(f'Could not create a chart entry for a chart: {e}')

                logging.info(f'{song} charts converted, saving')

                # Saves the chart in the ChartObject instance
                # Try except to avoid any crashes
                try:
                    songChart.save()
                except Exception as e:
                    logging.error(f'Could not save chart: {e}')

    # Accesses if the user selected the events
    if chartOptions['events']:

        # Accesses the scripts directory
        _pathsModRoot = Constants.FILE_LOCS.get('SCRIPTS_DIR')
        baseGameModRoot = _pathsModRoot[1]

        # Try except to avoid any errors
        try:
            # Creates the folder where the scripts should go
            folderMake(f'{result_folder}/{modFoldername}{baseGameModRoot}')

            # Writes neccessary scripts to the folder
            with open(f'{result_folder}/{modFoldername}{baseGameModRoot}{FileContents.CHANGE_CHARACTER_EVENT_HXC_NAME}', 'w') as scriptFile:
                scriptFile.write(FileContents.CHANGE_CHARACTER_EVENT_HXC_CONTENTS)
        except Exception as e:
            logging.error("Failed creating the scripts folder: " + e)

    # Accesses the character options selected by the user.
    if options.get('characters', {
            'assets': False
        })['assets']:
        logging.info('Copying character assets...')

        # Reads the path where the assets for characters are
        dir = Constants.FILE_LOCS.get('CHARACTERASSETS')
        psychCharacterAssets = modName + dir[0]
        bgCharacterAssets = dir[1]

        # Creates the folder for character assets
        folderMake(f'{result_folder}/{modFoldername}{bgCharacterAssets}')

        # Reads through all files in the character assets folder of Psych Engine
        for character in files.findAll(f'{psychCharacterAssets}*'):

            # Checks if the file is a file
            if Path(character).is_file():
                logging.info(f'Copying asset {character}')

                # Copies it
                # Try except to avoid any errors
                try:
                    fileCopy(character, result_folder + f'/{modFoldername}' + bgCharacterAssets + Path(character).name)
                except Exception as e:
                    logging.error(f'Could not copy asset {character}: {e}')
            else:
                logging.warn(f'{character} is a directory, not a file! Skipped')

    # Accesses the character options selected by the user.
    if options.get('characters', {
            'json': False
        })['json']:

        logging.info('Converting character jsons...')

        # Gets where character data should go
        dir = Constants.FILE_LOCS.get('CHARACTERJSONS')

        psychCharacters = modName + dir[0]
        bgCharacters = dir[1]

        # Creates the folder where the character assets should go
        folderMake(f'{result_folder}/{modFoldername}{bgCharacters}')

        # Finds all the files in the character data folder
        for character in files.findAll(f'{psychCharacters}*'):
            logging.info(f'Checking if {character} is a file...')
            
            # Checks if it ends with .json
            if Path(character).is_file() and character.endswith('.json'):

                # Creates a character object instance
                try:
                    converted_char = CharacterObject(character, result_folder + f'/{modFoldername}' + bgCharacters)

                    converted_char.convert()
                    converted_char.save()

                    # Ensures the character icon ID does not have 'icon-'
                    fileBasename = converted_char.iconID.replace('icon-', '')

                    # Checks if the icon ID exists in the character map
                    if fileBasename in characterMap:

                        # Appends it to the array of character names
                        characterMap[fileBasename].append(converted_char.characterName)
                    else:
                        # If it doesnt exist, create a new array
                        characterMap[fileBasename] = [converted_char.characterName]
                    logging.info(f'Saved {converted_char.characterName} to character map using their icon id: {fileBasename}.')
                except Exception as e:
                    logging.error(f'Failed to convert character {character}')
            else:
                logging.warn(f'{character} is a directory, or not a json! Skipped')

    # Accesses the character options selected by the user.
    if options.get('characters', {
        'icons': False
    })['icons']:
        logging.info('Copying character icons...')

        # Selects the paths to the character icons
        dir = Constants.FILE_LOCS.get('CHARACTERICON')
        psychCharacterAssets = modName + dir[0]
        bgCharacterAssets = dir[1]

        # Selects the paths to the freeplay icons
        freeplayDir = Constants.FILE_LOCS.get('FREEPLAYICON')[1]

        # Creates both necessary directories
        folderMake(f'{result_folder}/{modFoldername}{bgCharacterAssets}')
        folderMake(f'{result_folder}/{modFoldername}{freeplayDir}')

        # Finds all png files in the mod icons directory
        for character in files.findAll(f'{psychCharacterAssets}*.png'):
            # Checks if the character is a file
            if Path(character).is_file():
                logging.info(f'Copying asset {character}')

                # Try except to avoid any errors
                try:
                    filename = Path(character).name
                    # Some goofy ah mods don't name icons with icon-, causing them to be invalid in base game.
                    if not filename.startswith('icon-'):
                        logging.warn(f"Invalid icon name being renamed from '{filename}' to 'icon-{filename}'!")
                        filename = 'icon-' + filename
                    
                    destination = f'{result_folder}/{modFoldername}{bgCharacterAssets}{filename}'
                    # Copies the icon over
                    fileCopy(character, destination)

                    # Part 2, generating free play icons.
                    keyForThisIcon = filename.replace('icon-', '').replace('.png', '')
                    logging.info('Checking if ' + keyForThisIcon + ' is in the characterMap')

                    # Checks if the icon ID exists in the character map
                    if keyForThisIcon in characterMap:

                        # Try except to avoid any errors
                        try:
                            # Woah, freeplay icons

                            # Makes PIL shut up in our logs
                            logging.getLogger('PIL').setLevel(logging.INFO)

                            # Opens the icon with Image module
                            with Image.open(character) as img:
                                # Get the winning/normal half of icons
                                normal_half = img.crop((0, 0, 150, 150))
                                # Scale to 50x50, same size as BF and GF pixel icons
                                pixel_img = normal_half.resize((50, 50), Image.Resampling.NEAREST)

                                # Checks for every character assigned to this icon ID
                                for characterName in characterMap[keyForThisIcon]:

                                    # Defines the name of the file
                                    pixel_name = characterName + 'pixel.png'
                                    freeplay_destination = f'{result_folder}/{modFoldername}{freeplayDir}/{pixel_name}'

                                    # Saves the icon
                                    pixel_img.save(freeplay_destination)
                                    logging.info(f'Saving converted freeplay icon to {freeplay_destination}')
                        except Exception as ___exc:
                            logging.error(f"Failed to create character {keyForThisIcon}'s freeplay icon: {___exc}")
                except Exception as e:
                    logging.error(f'Could not copy asset {character}: {e}')

    # Accesses the song options selected by the user.
    songOptions = options.get('songs', {
        'inst': False,
        'voices': False,
        'split': False,
        'sounds': False,
        'music': False
    })
    if songOptions:

        # Opens the directory for songs folders
        dir = Constants.FILE_LOCS.get('SONGS')
        psychSongs = modName + dir[0]
        bgSongs = dir[1]

        # Finds all the song folders
        _allSongFiles = files.findAll(f'{psychSongs}*')

        # Iterate through them
        for song in _allSongFiles:

            # Get the song key
            _songKeyUnformatted = Path(song).name

            # Format it properly for Story Mode
            songKeyFormatted = _songKeyUnformatted.replace(' ', '-').lower()

            logging.info(f'Checking if {song} is a valid song directory...')

            # Checks if the song folder is a directory
            if Path(song).is_dir():
                logging.info(f'Copying files in {song}')

                # Get all files inside this song folder
                _allAudioFiles = files.findAll(f'{song}/*')

                # Iterate through all of them
                for songFile in _allAudioFiles:

                    # Get all the names of the files
                    _AllAudiosClear = [Path(__song).name for __song in _allAudioFiles]

                    # Check if this song folder is a Psych Engine 0.7.3 song folder
                    isPsych073Song =  'Voices-Opponent.ogg' in _AllAudiosClear and 'Voices-Player.ogg' in _AllAudiosClear

                    # Check if the audio file is an instrumental and instrumental option is selected
                    if Path(songFile).name == 'Inst.ogg' and songOptions['inst']:
                        logging.info(f'Copying asset {songFile}')

                        # Try except to avoid any errors
                        try:

                            # Create the folder using the formatted song key
                            folderMake(f'{result_folder}/{modFoldername}{bgSongs}{songKeyFormatted}')

                            # Copy the file to that folder we just created
                            fileCopy(songFile,
                              f'{result_folder}/{modFoldername}{bgSongs}{songKeyFormatted}/{Path(songFile).name}')
                        except Exception as e:
                            logging.error(f'Could not copy asset {songFile}: {e}')

                    # Check if there is a Voices.ogg file and Vocal Split is enabled, and it isn't a Psych Engine 0.7.3 song
                    elif Path(songFile).name == 'Voices.ogg' and songOptions['split'] and vocalSplitMasterToggle and not isPsych073Song:
                        # Vocal Split runs here

                        # Copy the song key
                        songKey = _songKeyUnformatted

                        # Define a new chart
                        chart = None

                        # Iterate through all charts
                        for _chart in charts:
                            # Check if this chart's key is the songKey
                            if _chart['songKey'] == songKey:
                                # Set the chart as this chart
                                chart = charts[charts.index(_chart)]

                        # Check if this chart isn't null
                        if chart != None:
                            # Uses the sections of the previously defined chart
                            sections = chart['sections']
                            # Gets the BPM
                            bpm = chart['bpm']
                            logging.info(f'Vocal Split ({songKey}) BPM is {bpm}')
                            
                            path = song + '/'
                            resultPath = result_folder + f'/{modFoldername}{bgSongs}{songKeyFormatted}/'

                            # Gets the characters of the metadata
                            songChars = [chart['player'],
                                          chart['opponent']]

                            logging.info(f'Vocal Split currently running for: {songKey}')
                            logging.info(f'Passed the following paths: {path} || {resultPath}')
                            logging.info(f'Passed characters: {songChars}')

                            # Run Vocal Split on a new thread
                            vocal_split_thread = threading.Thread(target=VocalSplit.vocalsplit, args=(sections, bpm, path, resultPath, songKey, songChars))

                            # Run the thread
                            vocal_split_thread.start()

                            # Wait for the thread to finish before continuing with any operations
                            vocal_split_thread.join()
                        else:

                            # If no chart was found, just copy the file
                            logging.warn(f'No chart was found for {songKey} so the vocal file will be copied instead.')

                            # Try except to avoid any errors
                            try:
                                # Make the folder where the file will go
                                folderMake(f'{result_folder}/{modFoldername}{bgSongs}{songKeyFormatted}')
                                # Copy the file
                                fileCopy(songFile,
                                f'{result_folder}/{modFoldername}{bgSongs}{songKeyFormatted}/{Path(songFile).name}')
                            except Exception as e:
                                logging.error(f'Could not copy asset {songFile}: {e}')

                    # If the song is a Psych Engine 0.7.3 song
                    elif isPsych073Song:

                        # Copy the song key unformatted
                        songKey = _songKeyUnformatted

                        # Create the folder
                        folderMake(f'{result_folder}/{modFoldername}{bgSongs}{songKeyFormatted}')

                        # Define a new chart
                        chart = None

                        # Iterate through the chart map to see if a chart has a song key
                        for _chart in charts:
                            # Look for the song key here
                            if _chart['songKey'] == songKey:
                                # Set the chart as this one
                                chart = charts[charts.index(_chart)]

                        # Check if the chart is valid
                        if chart != None:
                            # Try except to avoid any errors
                            try:
                                # Check if the file is Player audio
                                if Path(songFile).name == 'Voices-Player.ogg':
                                    # Copy it with Voices- + the player character
                                    fileCopy(songFile, f"{result_folder}/{modFoldername}{bgSongs}{songKeyFormatted}/Voices-{chart.metadata['playData']['characters'].get('player')}.ogg")
                                # Check if the file is Opponent audio
                                elif Path(songFile).name == 'Voices-Opponent.ogg':
                                    # Copy it with Voices- + the opponent character
                                    fileCopy(songFile, f"{result_folder}/{modFoldername}{bgSongs}{songKeyFormatted}/Voices-{chart.metadata['playData']['characters'].get('opponent')}.ogg")

                            except Exception as e:
                                logging.error(f'Could not copy asset {songFile}: {e}')

                        # If the chart isn't found, just copy it
                        else:
                            logging.warning(f'{songKeyFormatted} is a Psych Engine 0.7.3 song with separated vocals. Copy rename was attempted, however your chart was not found. These files will be copied instead.')
                            # Psst! If you were taken here, your chart is needed to set your character to the file!
                            fileCopy(songFile,
                              f'{result_folder}/{modFoldername}{bgSongs}{songKeyFormatted}/{Path(songFile).name}')
                    # Check if the user selected voices, as the final attempt to copy the file.
                    elif songOptions['voices']:
                        logging.info(f'Copying asset {songFile}')

                        # Warn Vocal Split is disabled and none other attempts could make it.
                        if not vocalSplitMasterToggle:
                            logging.warning('Vocal Split is disabled! This copy is the last.')

                        # Try except to avoid any errors
                        try:
                            # Create the folder
                            folderMake(f'{result_folder}/{modFoldername}{bgSongs}{songKeyFormatted}')
                            # Copy the file
                            fileCopy(songFile,
                              f'{result_folder}/{modFoldername}{bgSongs}{songKeyFormatted}/{Path(songFile).name}')
                        except Exception as e:
                            logging.error(f'Could not copy asset {songFile}: {e}')
            # End block for 'songs' folder

            # Check if the user selected sounds
            if songOptions['sounds']: # Some people use directories on sounds, so I am adding support

                # Get the paths to the sounds folder
                sounds_dir = Constants.FILE_LOCS.get('SOUNDS')
                psychSounds = modName + sounds_dir[0]
                baseSounds = sounds_dir[1]

                # Thankfully, glob ignores folders or files if they do not exist
                allsoundsindirsounds = files.findAll(f'{psychSounds}*')

                # Iterate through all the files and directories
                for asset in allsoundsindirsounds:
                    logging.info(f'Checking on {asset}')

                    # Check if it is a directory
                    if Path(asset).is_dir():
                        folderName = Path(asset).name
                        logging.info(f'{asset} is a tree, attempting to copy it')
                        # Try except to avoid any errors
                        try:
                            pathTo = f'{result_folder}/{modFoldername}{baseSounds}{folderName}'
                            # Copy it
                            treeCopy(asset, pathTo)
                        except Exception as e:
                            logging.error(f'Failed to copy {asset}: {e}')

                    # If it isn't a directory
                    else:
                        logging.info(f'{asset} is file, copying')

                        # Try except to avoid any errors
                        try:
                            # Make the folder where it should go
                            folderMake(f'{result_folder}/{modFoldername}{baseSounds}')
                            # Copy it
                            fileCopy(asset, f'{result_folder}/{modFoldername}{baseSounds}{Path(asset).name}')
                        except Exception as e:
                            logging.error(f'Failed to copy {asset}: {e}')

            # Get if the user selected sounds
            if songOptions['music']:
                # Get the paths to the music directory
                sounds_dir = Constants.FILE_LOCS.get('MUSIC')
                psychSounds = modName + sounds_dir[0]
                baseSounds = sounds_dir[1]

                # Get all the files (misleading variable name)
                allsoundsindirsounds = files.findAll(f'{psychSounds}*')
            
                # Iterate through all the files
                for asset in allsoundsindirsounds:
                    logging.info(f'Copying asset {asset}')
                    # Try except to avoid any errors
                    try:
                        # Make the folder
                        folderMake(f'{result_folder}/{modFoldername}{baseSounds}')
                        # Copy the file
                        fileCopy(asset,
                            f'{result_folder}/{modFoldername}{baseSounds}{Path(asset).name}')
                    except Exception as e:
                        logging.error(f'Could not copy asset {asset}: {e}')

    # Define the week conversion options
    weekCOptions = options.get('weeks', {
            'props': False, # Asset
            'levels': False,
            'titles': False # Asset
        })  
    # See if levels was selected from the week options
    if weekCOptions['levels']:
        logging.info('Converting weeks (levels)...')

        # Get the paths to the week files
        dir = Constants.FILE_LOCS.get('WEEKS')
        psychWeeks = modName + dir[0]
        baseLevels = dir[1]

        # Create the folder where the weeks should go
        folderMake(f'{result_folder}/{modFoldername}{baseLevels}')

        # Find all the jsons in the psych engine mod's weeks
        for week in files.findAll(f'{psychWeeks}*.json'):
            try:
                logging.info(f'Loading {week} into the converter...')

                # Open the json as a file
                weekJSON = json.loads(open(week, 'r').read())

                # Get the week key
                week_filename = Path(week).name

                # Convert the week
                converted_week = WeekTools.convert(weekJSON, modName, week_filename)
                
                # Write it to a new JSON file
                open(f'{result_folder}/{modFoldername}{baseLevels}{week_filename}', 'w').write(json.dumps(converted_week, indent=4))
            except Exception as e:
                logging.error(f'Error converting week {week}: {e}')

    # See if props was selected from the week options
    if weekCOptions['props']:
        logging.info('Copying prop assets...')

        # Get the paths to the character asset files
        dir = Constants.FILE_LOCS.get('WEEKCHARACTERASSET')
        psychWeeks = modName + dir[0]
        baseLevels = dir[1]

        # Get all xml files in the assets folder
        allXml = files.findAll(f'{psychWeeks}*.xml')

        # Get all png files in the assets folder
        allPng = files.findAll(f'{psychWeeks}*.png')

        # Combine and iterate
        for asset in allXml + allPng:
            logging.info(f'Copying {asset}')

            # Try except to avoid any errors
            try:
                # Create the folder where they should go
                folderMake(f'{result_folder}/{modFoldername}{baseLevels}')
                # Copy the file
                fileCopy(asset,
                    f'{result_folder}/{modFoldername}{baseLevels}{Path(asset).name}')
            except Exception as e:
                logging.error(f'Could not copy asset {asset}: {e}')

    # See if titles was selected from the week options
    if weekCOptions['titles']:
        logging.info('Copying level titles...')

        # Get the paths to the week images
        dir = Constants.FILE_LOCS.get('WEEKIMAGE')
        psychWeeks = f'{modName}{dir[0]}'
        baseLevels = dir[1]

        # Find all pngs there
        allPng = files.findAll(f'{psychWeeks}*.png')

        # Get all the pngs
        for asset in allPng:
            logging.info(f'Copying week title asset: {asset}')

            # Try except to avoid any errors
            try:
                # Make the folder
                folderMake(f'{result_folder}/{modFoldername}{baseLevels}')
                # Copy the file
                fileCopy(asset,
                    f'{result_folder}/{modFoldername}{baseLevels}{Path(asset).name}')
            except Exception as e:
                logging.error(f'Could not copy asset {asset}: {e}')
        #else: 
        #    logging.info(f'A week for {modName} has no story menu image, replacing with a default.')
        #    with open(f'week{modName}.png', 'wb') as fh:
        #        #id be surprised if this works
        #        try:
        #            folderMake(f'{result_folder}/{modFoldername}{baseLevels}')
        #            Image.open(base64.b64decode(data[Constants.BASE64_IMAGES.get('missingWeek')]))
        #            Image.save(f'{result_folder}/{modFoldername}{baseLevels}')
        #        except Exception as e:
        #            logging.error(f"Couldn't generate week image to {modFoldername}/{baseLevels}: {e}")

    # See if stages was selected
    if options.get('stages', False):
        logging.info('Converting stages...')

        # Get the paths to stages
        dir = Constants.FILE_LOCS.get('STAGE')
        psychStages = modName + dir[0]
        baseStages = dir[1]

        # Get all stage JSONS
        allStageJSON = files.findAll(f'{psychStages}*.json')
        # Iterate through all stage JSONS
        for asset in allStageJSON:
            logging.info(f'Converting {asset}')

            # Make the folder for the stages
            folderMake(f'{result_folder}/{modFoldername}{baseStages}')

            # Open the stage JSON as a json object
            stageJSON = json.loads(open(asset, 'r').read())

            # Get the path to it
            assetPath = f'{result_folder}/{modFoldername}{baseStages}{Path(asset).name}'
        
            # Get the lua path
            stageLua = asset.replace('.json', '.lua')
            logging.info(f'Parsing .lua with matching .json name: {stageLua}')

            # Build array of lua props
            luaProps = []

            # Check if the lua file exists
            if Path(stageLua).exists():
                logging.info(f'Parsing {stageLua} and attempting to extract methods and calls')

                # Try except to avoid any errors
                try:
                    # Assign props by reading and parsing the lua file
                    luaProps = StageLuaParse.parseStage(stageLua)
                except Exception as e:
                    logging.error(f'Could not complete parsing of {stageLua}: {e}')
                    continue

            logging.info(f'Converting Stage JSON')

            # Save the stage JSON as a JSON.
            stageJSONConverted = json.dumps(StageTool.convert(stageJSON, Path(asset).name, luaProps), indent=4)
            open(assetPath, 'w').write(stageJSONConverted)

    # Check if the user selected images
    if options.get('images'): # Images include XMLs
        logging.info('Copying images')

        # Get the path to the images folder
        dir = Constants.FILE_LOCS.get('IMAGES')
        psychImages = modName + dir[0]
        baseImages = dir[1]

        # Find all files in the images folder
        allimagesandfolders = files.findAll(f'{psychImages}*')
        for asset in allimagesandfolders:
            logging.info(f'Checking on {asset}')

            # For directories, to make sure we don't copy directories by Psych Engine 
            if Path(asset).is_dir():
                logging.info(f'{asset} is directory, checking if it should be excluded...')

                # Get the folder's name
                folderName = Path(asset).name

                # Check if this folder is not in the exclude list
                if not folderName in Constants.EXCLUDE_FOLDERS_IMAGES['PsychEngine']:
                    logging.info(f'{asset} is not excluded... attempting to copy.')
                    # Try except to avoid any errors
                    try:
                        pathTo = f'{result_folder}/{modFoldername}{baseImages}{folderName}'
                        # Copy it
                        treeCopy(asset, pathTo)
                    except Exception as e:
                        logging.error(f'Failed to copy {asset}: {e}')
                else:
                    # It is excluded
                    logging.warn(f'{asset} is excluded. Skipped')

            else:
                # It is a file
                logging.info(f'{asset} is file, copying')

                # Try except to avoid any errors
                try:
                    # Make the folder
                    folderMake(f'{result_folder}/{modFoldername}{baseImages}')
                    # Copy the file
                    fileCopy(asset, f'{result_folder}/{modFoldername}{baseImages}{Path(asset).name}')
                except Exception as e:
                    logging.error(f'Failed to copy {asset}: {e}')

    # Complete the conversion by announcing it has completed
    logging.info(Utils.coolText("CONVERSION COMPLETED"))

    # Announce how long it took to convert it
    logging.info(f'Conversion done: Took {time.time() - runtime}s')

