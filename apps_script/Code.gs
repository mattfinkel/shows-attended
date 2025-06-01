// Configuration
function getConfig() {
  try {
    const scriptProperties = PropertiesService.getScriptProperties();
    const appId = scriptProperties.getProperty('APP_ID');
    const accessKey = scriptProperties.getProperty('ACCESS_KEY');
    
    Logger.log('Retrieved credentials:', { 
      hasAppId: !!appId, 
      hasAccessKey: !!accessKey 
    });
    
    if (!appId || !accessKey) {
      Logger.log('Error: Missing credentials');
      throw new Error('AppSheet credentials not configured');
    }
    
    return {
      APP_ID: appId,
      ACCESS_KEY: accessKey,
      API_BASE_URL: `https://api.appsheet.com/api/v2/apps/${appId}/tables`
    };
  } catch (error) {
    Logger.log('Error in getConfig:', error);
    throw error;
  }
}

// Serve the HTML page
function doGet() {
  try {
    Logger.log('Starting doGet function');
    
    // Verify credentials are configured
    const config = getConfig();
    Logger.log('Config loaded successfully');
    
    Logger.log('Loading show_entry template');
    const template = HtmlService.createTemplateFromFile('show_entry');
    Logger.log('Template created');
    
    const output = template.evaluate()
      .setTitle('Add New Show')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
    Logger.log('Template evaluated');
    
    return output;
  } catch (error) {
    Logger.log('Error in doGet:', error);
    return HtmlService.createHtmlOutput(`
      <h1>Error: ${error.message}</h1>
      <p>Please set up your credentials in the Apps Script editor:</p>
      <ol>
        <li>Open the Apps Script editor</li>
        <li>Click on "Project Settings" (gear icon)</li>
        <li>Go to the "Script Properties" tab</li>
        <li>Add two properties:
          <ul>
            <li>APP_ID: Your AppSheet App ID</li>
            <li>ACCESS_KEY: Your AppSheet Access Key</li>
          </ul>
        </li>
      </ol>
      <p>Error details: ${error.message}</p>
    `);
  }
}

// Save credentials securely
function saveCredentials(appId, accessKey) {
  const scriptProperties = PropertiesService.getScriptProperties();
  scriptProperties.setProperties({
    'APP_ID': appId,
    'ACCESS_KEY': accessKey
  });
  return 'Credentials saved successfully!';
}

// Get all venues from AppSheet
function getVenues() {
  const response = makeAppSheetRequest('VenueList', 'Find');
  return response.Rows.map(row => row.Name);
}

// Get all events from AppSheet
function getEvents() {
  const response = makeAppSheetRequest('Events', 'Find');
  return response.Rows.map(row => row.Name);
}

// Check if a band exists
function checkBand(bandName) {
  const response = makeAppSheetRequest('Bands', 'Find');
  return response.Rows.some(row => row.Name === bandName);
}

// Add a new show
function addShow(showData) {
  try {
    // 1. Get or create venue
    const venueId = getOrCreateVenue(showData.venue);
    
    // 2. Get or create event if provided
    let eventId = null;
    if (showData.event) {
      eventId = getOrCreateEvent(showData.event);
    }
    
    // 3. Create the show
    const showId = createShow(showData, venueId, eventId);
    
    // 4. Add bands
    addBandsToShow(showData.bands, showId);
    
    // 5. Add attendance if checked
    if (showData.attended) {
      addAttendance(showId);
    }
    
    return { success: true, message: 'Show added successfully' };
  } catch (error) {
    console.error('Error adding show:', error);
    throw new Error(error.message || 'Failed to add show');
  }
}

// Helper function to make AppSheet API requests
function makeAppSheetRequest(tableName, action, data = {}) {
  const config = getConfig();
  const url = `${config.API_BASE_URL}/${tableName}/data`;
  const payload = {
    Action: action,
    Properties: {
      Locale: "en-US"
    },
    ...data
  };
  
  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'ApplicationAccessKey': config.ACCESS_KEY
    },
    payload: JSON.stringify(payload)
  };
  
  const response = UrlFetchApp.fetch(url, options);
  return JSON.parse(response.getContentText());
}

// Get or create a venue
function getOrCreateVenue(venueName) {
  // First try to find existing venue
  const response = makeAppSheetRequest('VenueList', 'Find');
  const existingVenue = response.Rows.find(row => row.Name === venueName);
  
  if (existingVenue) {
    return existingVenue['Row ID'];
  }
  
  // Create new venue
  const newVenue = makeAppSheetRequest('VenueList', 'Add', {
    Rows: [{
      Name: venueName,
      Location: '',  // You might want to prompt for this
      Closed: false
    }]
  });
  
  return newVenue.Rows[0]['Row ID'];
}

// Get or create an event
function getOrCreateEvent(eventName) {
  // First try to find existing event
  const response = makeAppSheetRequest('Events', 'Find');
  const existingEvent = response.Rows.find(row => row.Name === eventName);
  
  if (existingEvent) {
    return existingEvent['Row ID'];
  }
  
  // Create new event
  const newEvent = makeAppSheetRequest('Events', 'Add', {
    Rows: [{
      Name: eventName
    }]
  });
  
  return newEvent.Rows[0]['Row ID'];
}

// Create a new show
function createShow(showData, venueId, eventId) {
  const show = makeAppSheetRequest('ShowList', 'Add', {
    Rows: [{
      Date: showData.date,
      VenueID: venueId,
      EventID: eventId,
      Confirmed: showData.confirmed,
      Notes: showData.notes
    }]
  });
  
  return show.Rows[0]['Row ID'];
}

// Add bands to a show
function addBandsToShow(bands, showId) {
  // Get existing bands
  const response = makeAppSheetRequest('Bands', 'Find');
  const existingBands = response.Rows;
  
  // Process each band
  bands.forEach((bandName, index) => {
    // Find or create band
    let bandId = existingBands.find(b => b.Name === bandName)?.['Row ID'];
    
    if (!bandId) {
      // Create new band
      const newBand = makeAppSheetRequest('Bands', 'Add', {
        Rows: [{
          Name: bandName
        }]
      });
      bandId = newBand.Rows[0]['Row ID'];
    }
    
    // Add band to show
    makeAppSheetRequest('Show_Bands', 'Add', {
      Rows: [{
        ShowID: showId,
        BandID: bandId,
        Order: index + 1
      }]
    });
  });
}

// Add attendance record
function addAttendance(showId) {
  // Get Sarah's ID
  const response = makeAppSheetRequest('Attendees', 'Find');
  const sarah = response.Rows.find(row => row.Name === 'Sarah');
  
  if (sarah) {
    makeAppSheetRequest('Show_Attendees', 'Add', {
      Rows: [{
        ShowID: showId,
        AttendeeID: sarah['Row ID']
      }]
    });
  }
} 