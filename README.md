# AIS Linker
A tool for overlaying AIS tracks on photobot images, and recording vessel traffic.

#### Setup
This tool requires Python 3 with PyQt5 added.

While this tool can be downloaded and used anywhere, it relies on a number of folders and files in its local folder. When multiple people use this tool, it is highly recommended to use it from a single networked location accessable to everyone using it.

Run the tool by running "<span>start.py</span>". Depending on your python setup, you may be able to simply double click this file, but you might need to use a command line command such as `python start.py` or `python3 start.py`.

#### Loading Data

When you start this tool, it will prompt you to select a "contacts" database, then a "calibration" database.

Contact databases are each a separate, processed data set. When generating a report, only the currently selected contact database will be considered. A single camera may have multiple contact databases if it is processed in different ways.

Calibration databases contain the physical location of the camera and reference points in the image, as well as any images that have been specifically calibrated by a user. This is also linked to (and automatically loads) an AIS database, which contains processed AIS information for the area.

While the tool is running, these can both be changed at any time using the "Change contacts database" in the file menu.

Finally, images will need to be loaded to process (this can be skipped when opening the tool to generate reports). This is done through the "Load images" button in the file menu, which prompts the user to select a folder. When selecting the folder, all images immediately in that folder are loaded, but any subfolders and unrecognized files are ignored.

Even when using this tool remotely, it is highly recommended to use a local copy of the images. This dramatically improves loading times when moving through images.

#### General Navigation

When viewing an image, right clicking toggles zooming in/zooming out. Left clicking marks a contact.

On the right side of the display in order from top to bottom is the date and time, a box for currently nearby AIS tracks, a box for creating contacts, and controls for navigating the images.

A daily count of the number of contacts (note: these are UTC daily totals) is displayed just above the controls. Notably, this can also be helpful by showing whether anything has already been processed for the currently selected day.

#### Marking Contacts

Mark a contact by left clicking on the image. Note that if positions are important, the contact needs to be marked _specically on the waterline_, at a consistent position in the ship.

The type of contact selected will determine what options are avaiable, but additional information can always be added in the text box. Commas can be used to add multiple different tags in this box. Of note are the following options:
 * Vessels selected as "AIS" vessels must be linked to an AIS (by selecting the "link" button next to the relevant track) before they can be saved
 * The type of information that is important depends on the analysis being performed. Not all options need to be chosen from before saving a contact.
 * Contacts that have the "repeat" box checked are ignored from most types of reports.

Different types of contacts are displayed using different colours. A contact can be modified or deleted by left clicking on the contact marker, and then performing the appropriate action.

#### Other File Menu Options

 * Save contacts: immediately saves the current contact database. In general this is unnecessary as the tool automatically saves the contacts when switching days and when closing the tool, but it may be desirable to force save the database in certain situations.
 * Calibrate mode: allows the calibration the tool for more precise distances.

#### Display Options

Several display options are available to make identifying which ais tracks belong to which vessels easier.
 * Limit AIS display distance: if enabled, limits the AIS lines drawn to 2km from the camera. This can help when distant lines, especially those that are moving behind islands, are obscuring the image.
 * toggle display time: determines how far in front or behind of the current AIS position to draw lines. Shorter times make it easier to map busier locations, but longer times make it easier to catch markers when the times on images aren't exactly matching those of the AIS data. Toggles between 1, 2, and 5 minutes.

#### Creating Reports

Todo: descriptiions of each report type

#### Calibrate Mode

Todo.

#### todo:

 * Crashes when 'meta.txt' is missing in main folder
 * add default image? Check licence
 * add options to create new databases, archive databases, and restore archived databases
 * change window title
 * Better calibration indicators?
 * Better "modify contact" menu