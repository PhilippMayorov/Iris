#!/usr/bin/env python3
"""
Script to read all MacBook contacts using PyObjC and the Contacts framework.
"""

import sys
import json
from datetime import datetime
from Contacts import CNContactStore, CNContact, CNContactFormatter
from Contacts import CNContactGivenNameKey, CNContactFamilyNameKey, CNContactNicknameKey
from Contacts import CNContactPhoneNumbersKey, CNContactEmailAddressesKey, CNContactPostalAddressesKey
from Contacts import CNContactBirthdayKey, CNContactJobTitleKey, CNContactDepartmentNameKey
from Contacts import CNContactOrganizationNameKey, CNContactMiddleNameKey, CNContactNoteKey
from Contacts import CNContactImageDataKey, CNContactThumbnailImageDataKey
from Contacts import CNContactUrlAddressesKey, CNContactInstantMessageAddressesKey, CNContactSocialProfilesKey
from Foundation import NSData, NSString
import Contacts

def request_contacts_permission():
    """Request permission to access contacts."""
    store = CNContactStore()
    
    # Check current authorization status
    auth_status = Contacts.CNContactStore.authorizationStatusForEntityType_(Contacts.CNEntityTypeContacts)
    
    if auth_status == Contacts.CNAuthorizationStatusAuthorized:
        print("✅ Contacts access already authorized")
        return True
    elif auth_status == Contacts.CNAuthorizationStatusDenied:
        print("❌ Contacts access denied. Please enable in System Preferences > Security & Privacy > Privacy > Contacts")
        return False
    elif auth_status == Contacts.CNAuthorizationStatusRestricted:
        print("❌ Contacts access restricted (e.g., by parental controls)")
        return False
    else:
        print("🔐 Requesting contacts permission...")
        # Request access
        result = store.requestAccessForEntityType_completionHandler_(
            Contacts.CNEntityTypeContacts, 
            lambda granted, error: None
        )
        # Note: The completion handler is asynchronous, so we need to check again
        import time
        time.sleep(1)  # Give it a moment to process
        auth_status = Contacts.CNContactStore.authorizationStatusForEntityType_(Contacts.CNEntityTypeContacts)
        if auth_status == Contacts.CNAuthorizationStatusAuthorized:
            print("✅ Contacts access granted")
            return True
        else:
            print("❌ Contacts access denied")
            return False

def get_all_contacts():
    """Retrieve all contacts from the MacBook."""
    store = CNContactStore()
    
    # Define the keys we want to fetch
    keys_to_fetch = [
        CNContactGivenNameKey,
        CNContactFamilyNameKey,
        CNContactNicknameKey,
        CNContactMiddleNameKey,
        CNContactPhoneNumbersKey,
        CNContactEmailAddressesKey,
        CNContactPostalAddressesKey,
        CNContactBirthdayKey,
        CNContactJobTitleKey,
        CNContactDepartmentNameKey,
        CNContactOrganizationNameKey,
        CNContactNoteKey,
        CNContactImageDataKey,
        CNContactThumbnailImageDataKey,
        CNContactUrlAddressesKey,
        CNContactInstantMessageAddressesKey,
        CNContactSocialProfilesKey
    ]
    
    # Create a fetch request
    request = Contacts.CNContactFetchRequest.alloc().initWithKeysToFetch_(keys_to_fetch)
    
    # Fetch all contacts
    contacts = []
    error = None
    
    def fetch_contacts():
        nonlocal contacts, error
        try:
            # Use the correct method to enumerate contacts
            def contact_enumeration_handler(contact, stop):
                contacts.append(contact)
            
            store.enumerateContactsWithFetchRequest_error_usingBlock_(
                request, None, contact_enumeration_handler
            )
        except Exception as e:
            error = e
    
    fetch_contacts()
    
    if error:
        print(f"❌ Error fetching contacts: {error}")
        return []
    
    return contacts

def format_contact_data(contact):
    """Format contact data into a Python dictionary."""
    
    def safe_get(contact, method_name, default=''):
        """Safely get a contact property, handling cases where it wasn't fetched."""
        try:
            method = getattr(contact, method_name)
            result = method()
            return str(result) if result else default
        except:
            return default
    
    contact_data = {
        'identifier': str(contact.identifier()),
        'firstName': safe_get(contact, 'givenName'),
        'lastName': safe_get(contact, 'familyName'),
        'middleName': safe_get(contact, 'middleName'),
        'nickname': safe_get(contact, 'nickname'),
        'jobTitle': safe_get(contact, 'jobTitle'),
        'departmentName': safe_get(contact, 'departmentName'),
        'organizationName': safe_get(contact, 'organizationName'),
        'note': safe_get(contact, 'note'),
        'phoneNumbers': [],
        'emailAddresses': [],
        'postalAddresses': [],
        'urlAddresses': [],
        'instantMessageAddresses': [],
        'socialProfiles': [],
        'birthday': '',
        'hasImage': False,
        'hasThumbnail': False
    }
    
    # Handle birthday
    try:
        birthday = contact.birthday()
        if birthday and birthday.year() and birthday.month() and birthday.day():
            contact_data['birthday'] = f"{birthday.year():04d}-{birthday.month():02d}-{birthday.day():02d}"
    except:
        pass
    
    # Handle phone numbers
    try:
        for phone in contact.phoneNumbers():
            phone_data = {
                'label': str(phone.label()) if phone.label() else 'Other',
                'value': str(phone.value().stringValue()) if phone.value() else ''
            }
            contact_data['phoneNumbers'].append(phone_data)
    except:
        pass
    
    # Handle email addresses
    try:
        for email in contact.emailAddresses():
            email_data = {
                'label': str(email.label()) if email.label() else 'Other',
                'value': str(email.value()) if email.value() else ''
            }
            contact_data['emailAddresses'].append(email_data)
    except:
        pass
    
    # Handle postal addresses
    try:
        for address in contact.postalAddresses():
            addr = address.value()
            address_data = {
                'label': str(address.label()) if address.label() else 'Other',
                'street': str(addr.street()) if addr.street() else '',
                'city': str(addr.city()) if addr.city() else '',
                'state': str(addr.state()) if addr.state() else '',
                'postalCode': str(addr.postalCode()) if addr.postalCode() else '',
                'country': str(addr.country()) if addr.country() else '',
                'formatted': str(CNContactFormatter.stringFromPostalAddress_style_(addr, CNContactFormatterStyleMailingAddress))
            }
            contact_data['postalAddresses'].append(address_data)
    except:
        pass
    
    # Handle URL addresses
    try:
        for url in contact.urlAddresses():
            url_data = {
                'label': str(url.label()) if url.label() else 'Other',
                'value': str(url.value()) if url.value() else ''
            }
            contact_data['urlAddresses'].append(url_data)
    except:
        pass
    
    # Handle instant message addresses
    try:
        for im in contact.instantMessageAddresses():
            im_data = {
                'label': str(im.label()) if im.label() else 'Other',
                'service': str(im.value().service()) if im.value() else '',
                'username': str(im.value().username()) if im.value() else ''
            }
            contact_data['instantMessageAddresses'].append(im_data)
    except:
        pass
    
    # Handle social profiles
    try:
        for social in contact.socialProfiles():
            social_data = {
                'label': str(social.label()) if social.label() else 'Other',
                'service': str(social.value().service()) if social.value() else '',
                'username': str(social.value().username()) if social.value() else '',
                'urlString': str(social.value().urlString()) if social.value() else ''
            }
            contact_data['socialProfiles'].append(social_data)
    except:
        pass
    
    # Check for images
    try:
        contact_data['hasImage'] = contact.imageData() is not None
    except:
        contact_data['hasImage'] = False
    
    try:
        contact_data['hasThumbnail'] = contact.thumbnailImageData() is not None
    except:
        contact_data['hasThumbnail'] = False
    
    return contact_data

def display_contacts_summary(contacts_data):
    """Display a summary of all contacts."""
    print(f"\n📱 CONTACTS SUMMARY")
    print(f"{'='*50}")
    print(f"Total contacts: {len(contacts_data)}")
    
    # Count contacts with different types of information
    with_phones = sum(1 for c in contacts_data if c['phoneNumbers'])
    with_emails = sum(1 for c in contacts_data if c['emailAddresses'])
    with_addresses = sum(1 for c in contacts_data if c['postalAddresses'])
    with_images = sum(1 for c in contacts_data if c['hasImage'])
    
    print(f"Contacts with phone numbers: {with_phones}")
    print(f"Contacts with email addresses: {with_emails}")
    print(f"Contacts with postal addresses: {with_addresses}")
    print(f"Contacts with profile images: {with_images}")
    
    # Show first 10 contacts as examples
    print(f"\n📋 FIRST 10 CONTACTS:")
    print(f"{'='*50}")
    
    for i, contact in enumerate(contacts_data[:10]):
        name = f"{contact['firstName']} {contact['lastName']}".strip()
        if not name:
            name = contact['nickname'] or "Unnamed Contact"
        
        print(f"{i+1:2d}. {name}")
        if contact['phoneNumbers']:
            print(f"     📞 {contact['phoneNumbers'][0]['value']}")
        if contact['emailAddresses']:
            print(f"     📧 {contact['emailAddresses'][0]['value']}")
        if contact['organizationName']:
            print(f"     🏢 {contact['organizationName']}")
        print()

def save_contacts_to_file(contacts_data, filename="contacts_export.json"):
    """Save contacts to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(contacts_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Contacts saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving contacts: {e}")

def main():
    """Main function to read and display contacts."""
    print("🔍 MacBook Contacts Reader")
    print("="*50)
    
    # Request permission
    if not request_contacts_permission():
        print("❌ Cannot proceed without contacts permission")
        sys.exit(1)
    
    # Get all contacts
    print("\n📖 Reading contacts...")
    contacts = get_all_contacts()
    
    if not contacts:
        print("❌ No contacts found or error occurred")
        sys.exit(1)
    
    # Format contact data
    print("🔄 Formatting contact data...")
    contacts_data = [format_contact_data(contact) for contact in contacts]
    
    # Display summary
    display_contacts_summary(contacts_data)
    
    # Save to file
    save_contacts_to_file(contacts_data)
    
    print(f"\n✅ Successfully read {len(contacts_data)} contacts!")
    print("📄 Full contact data has been saved to 'contacts_export.json'")

if __name__ == "__main__":
    main()
