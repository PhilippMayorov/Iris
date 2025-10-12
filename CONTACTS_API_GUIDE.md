# Contacts API Guide

This guide explains how to use the new contacts API endpoints in the Iris frontend application.

## Overview

The contacts API allows you to access and filter your MacBook contacts through HTTP endpoints. It uses the macOS Contacts framework via PyObjC to read contact data directly from your system.

## Endpoints

### 1. Get Contacts Statistics
**GET** `/api/contacts/stats`

Returns statistics about your contacts.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_contacts": 328,
    "contacts_with_email": 32,
    "contacts_with_phone": 323,
    "contacts_with_address": 0,
    "contacts_with_image": 45,
    "contacts_with_organization": 20,
    "contacts_with_birthday": 44
  }
}
```

### 2. Get All Contacts (with filtering)
**GET** `/api/contacts`

Retrieves contacts with optional filtering and pagination.

**Query Parameters:**
- `has_email` (boolean): Filter contacts that have email addresses
- `has_phone` (boolean): Filter contacts that have phone numbers
- `has_address` (boolean): Filter contacts that have postal addresses
- `has_image` (boolean): Filter contacts that have profile images
- `name_contains` (string): Filter contacts whose name contains this text
- `organization_contains` (string): Filter contacts whose organization contains this text
- `limit` (integer): Maximum number of contacts to return (default: 100)
- `offset` (integer): Number of contacts to skip (default: 0)

**Example Requests:**
```bash
# Get all contacts
curl "http://127.0.0.1:5001/api/contacts"

# Get only contacts with email addresses
curl "http://127.0.0.1:5001/api/contacts?has_email=true"

# Get contacts with phone numbers, limit to 10
curl "http://127.0.0.1:5001/api/contacts?has_phone=true&limit=10"

# Search for contacts with "John" in their name
curl "http://127.0.0.1:5001/api/contacts?name_contains=John"

# Get contacts from a specific organization
curl "http://127.0.0.1:5001/api/contacts?organization_contains=Apple"
```

**Response:**
```json
{
  "success": true,
  "contacts": [
    {
      "identifier": "74C15941-A9EE-4E30-B70D-F31A060389D9:ABPerson",
      "firstName": "Daniel",
      "lastName": "Petlach",
      "middleName": "",
      "nickname": "",
      "jobTitle": "",
      "departmentName": "",
      "organizationName": "",
      "note": "",
      "phoneNumbers": [
        {
          "label": "Other",
          "value": "647 921 8714"
        }
      ],
      "emailAddresses": [
        {
          "label": "Other",
          "value": "daniel.petlach@gmail.com"
        }
      ],
      "postalAddresses": [],
      "urlAddresses": [],
      "instantMessageAddresses": [],
      "socialProfiles": [],
      "birthday": "",
      "hasImage": false,
      "hasThumbnail": false
    }
  ],
  "pagination": {
    "limit": 100,
    "offset": 0,
    "total_count": 328,
    "filtered_count": 32,
    "has_more": false
  },
  "filters_applied": {
    "has_email": true
  },
  "statistics": {
    "total_contacts": 328,
    "filtered_contacts": 32,
    "returned_contacts": 32,
    "contacts_with_email": 32,
    "contacts_with_phone": 323,
    "contacts_with_address": 0,
    "contacts_with_image": 45
  }
}
```

### 3. Search Contacts
**POST** `/api/contacts/search`

Advanced search functionality with text search and filtering.

**Request Body:**
```json
{
  "query": "search text",
  "filters": {
    "has_email": true,
    "has_phone": false,
    "has_address": false,
    "has_image": false,
    "name_contains": "John",
    "organization_contains": "Apple"
  },
  "limit": 50,
  "offset": 0
}
```

**Example Request:**
```bash
curl -X POST "http://127.0.0.1:5001/api/contacts/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Petlach",
    "filters": {
      "has_email": true
    },
    "limit": 5
  }'
```

**Response:**
```json
{
  "success": true,
  "contacts": [...],
  "search_query": "Petlach",
  "pagination": {
    "limit": 5,
    "offset": 0,
    "total_count": 8,
    "has_more": true
  },
  "filters_applied": {
    "has_email": true
  }
}
```

## Contact Data Structure

Each contact object contains the following fields:

- `identifier`: Unique contact identifier
- `firstName`: Contact's first name
- `lastName`: Contact's last name
- `middleName`: Contact's middle name
- `nickname`: Contact's nickname
- `jobTitle`: Contact's job title
- `departmentName`: Contact's department
- `organizationName`: Contact's organization
- `note`: Contact notes
- `phoneNumbers`: Array of phone number objects with `label` and `value`
- `emailAddresses`: Array of email objects with `label` and `value`
- `postalAddresses`: Array of address objects with detailed address fields
- `urlAddresses`: Array of URL objects with `label` and `value`
- `instantMessageAddresses`: Array of IM objects with service and username
- `socialProfiles`: Array of social profile objects
- `birthday`: Birthday in YYYY-MM-DD format
- `hasImage`: Boolean indicating if contact has a profile image
- `hasThumbnail`: Boolean indicating if contact has a thumbnail image

## Filtering Options

### Boolean Filters
- `has_email`: Only contacts with email addresses
- `has_phone`: Only contacts with phone numbers
- `has_address`: Only contacts with postal addresses
- `has_image`: Only contacts with profile images

### Text Filters
- `name_contains`: Search in first name, last name, and nickname
- `organization_contains`: Search in organization name

### Search Query
The search query in the POST endpoint searches across:
- Full name (first + last name)
- Nickname
- Organization name
- Job title
- Email addresses
- Phone numbers

## Error Handling

If the contacts framework is not available (e.g., not on macOS or PyObjC not installed), the API will return:

```json
{
  "success": false,
  "error": "Contacts framework not available. This feature requires macOS and PyObjC."
}
```

## Usage Examples

### Get all contacts with email addresses
```bash
curl "http://127.0.0.1:5001/api/contacts?has_email=true"
```

### Search for contacts by name
```bash
curl -X POST "http://127.0.0.1:5001/api/contacts/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "John"}'
```

### Get contacts from a specific company
```bash
curl "http://127.0.0.1:5001/api/contacts?organization_contains=Apple&limit=20"
```

### Get contacts with profile images
```bash
curl "http://127.0.0.1:5001/api/contacts?has_image=true"
```

## Integration with Iris

These endpoints are now available in your Iris frontend application and can be used to:

1. **Email Integration**: Find contacts with email addresses for sending emails
2. **Voice Commands**: Search for contacts by name when using voice commands
3. **Contact Management**: Display and filter your contacts in the web interface
4. **Data Analysis**: Get statistics about your contact database

The contacts data is read directly from your MacBook's Contacts app, so it's always up-to-date with your current contact information.
