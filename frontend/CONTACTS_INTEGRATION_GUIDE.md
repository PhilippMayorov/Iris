# Contacts API Integration Guide for Frontend

This guide explains when and how to use the contacts API endpoints in the Iris frontend application.

## Overview

The contacts API provides access to the user's MacBook contacts, enabling intelligent contact resolution, email suggestions, and enhanced user experience. This guide covers appropriate use cases and implementation patterns.

## When to Use Contacts API

### 1. **Email Address Resolution** 🎯
**Use Case**: User mentions a name but you need to find their email address.

**Scenario**: 
- User says: "Send an email to John about the meeting"
- Frontend needs to resolve "John" to an actual email address

**Implementation**:
```javascript
// Search for contacts matching the name
const searchContacts = async (name) => {
  const response = await fetch('/api/contacts/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: name,
      filters: { has_email: true },
      limit: 5
    })
  });
  return response.json();
};

// Usage in email composition
const resolveEmailAddress = async (name) => {
  const result = await searchContacts(name);
  if (result.success && result.contacts.length > 0) {
    // Show email options to user
    return result.contacts.map(contact => ({
      name: `${contact.firstName} ${contact.lastName}`.trim(),
      email: contact.emailAddresses[0].value,
      fullContact: contact
    }));
  }
  return [];
};
```

### 2. **Contact Validation** ✅
**Use Case**: Verify if a contact exists before sending emails or making calls.

**Scenario**:
- User says: "Call Sarah"
- Frontend should check if Sarah exists in contacts and has a phone number

**Implementation**:
```javascript
const validateContact = async (name, type = 'phone') => {
  const filters = type === 'phone' ? { has_phone: true } : { has_email: true };
  
  const response = await fetch('/api/contacts/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: name,
      filters: filters,
      limit: 1
    })
  });
  
  const result = await response.json();
  return result.success && result.contacts.length > 0;
};
```

### 3. **Smart Contact Suggestions** 💡
**Use Case**: Provide intelligent suggestions when user is typing or speaking.

**Scenario**:
- User starts typing "John" in an email field
- Frontend shows matching contacts with their email addresses

**Implementation**:
```javascript
const getContactSuggestions = async (query) => {
  if (query.length < 2) return [];
  
  const response = await fetch('/api/contacts/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: query,
      filters: { has_email: true },
      limit: 10
    })
  });
  
  const result = await response.json();
  if (result.success) {
    return result.contacts.map(contact => ({
      displayName: `${contact.firstName} ${contact.lastName}`.trim() || contact.nickname,
      email: contact.emailAddresses[0]?.value,
      phone: contact.phoneNumbers[0]?.value,
      organization: contact.organizationName
    }));
  }
  return [];
};
```

### 4. **Contact Information Display** 📋
**Use Case**: Show comprehensive contact information in the UI.

**Scenario**:
- User asks: "What's John's phone number?"
- Frontend displays John's contact details

**Implementation**:
```javascript
const getContactDetails = async (name) => {
  const response = await fetch('/api/contacts/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: name,
      limit: 1
    })
  });
  
  const result = await response.json();
  if (result.success && result.contacts.length > 0) {
    const contact = result.contacts[0];
    return {
      name: `${contact.firstName} ${contact.lastName}`.trim(),
      emails: contact.emailAddresses,
      phones: contact.phoneNumbers,
      organization: contact.organizationName,
      jobTitle: contact.jobTitle,
      hasImage: contact.hasImage
    };
  }
  return null;
};
```

### 5. **Voice Command Enhancement** 🎤
**Use Case**: Enhance voice commands with contact context.

**Scenario**:
- User says: "Send an email to my boss"
- Frontend needs to identify who "my boss" is from contacts

**Implementation**:
```javascript
const resolveContactReference = async (reference) => {
  // Common relationship mappings
  const relationshipMappings = {
    'boss': ['manager', 'supervisor', 'director'],
    'mom': ['mother', 'mommy'],
    'dad': ['father', 'daddy'],
    'wife': ['spouse', 'partner'],
    'husband': ['spouse', 'partner']
  };
  
  const searchTerms = relationshipMappings[reference.toLowerCase()] || [reference];
  
  for (const term of searchTerms) {
    const response = await fetch('/api/contacts/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: term,
        filters: { has_email: true },
        limit: 5
      })
    });
    
    const result = await response.json();
    if (result.success && result.contacts.length > 0) {
      return result.contacts;
    }
  }
  return [];
};
```

### 6. **Contact Statistics Dashboard** 📊
**Use Case**: Display contact database insights.

**Scenario**:
- User wants to see overview of their contacts
- Frontend shows statistics and insights

**Implementation**:
```javascript
const getContactStats = async () => {
  const response = await fetch('/api/contacts/stats');
  const result = await response.json();
  
  if (result.success) {
    return {
      total: result.stats.total_contacts,
      withEmail: result.stats.contacts_with_email,
      withPhone: result.stats.contacts_with_phone,
      withImage: result.stats.contacts_with_image,
      withOrganization: result.stats.contacts_with_organization
    };
  }
  return null;
};
```

## Integration Patterns

### 1. **Email Composition Enhancement**
```javascript
// In email composition component
const EmailComposer = () => {
  const [recipients, setRecipients] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  
  const handleRecipientInput = async (value) => {
    if (value.includes('@')) {
      // It's already an email, no need to search
      return;
    }
    
    const contacts = await getContactSuggestions(value);
    setSuggestions(contacts);
  };
  
  const selectContact = (contact) => {
    setRecipients([...recipients, {
      name: contact.displayName,
      email: contact.email
    }]);
    setSuggestions([]);
  };
  
  return (
    <div>
      <input 
        placeholder="To: name or email"
        onChange={(e) => handleRecipientInput(e.target.value)}
      />
      {suggestions.length > 0 && (
        <div className="suggestions">
          {suggestions.map(contact => (
            <div key={contact.email} onClick={() => selectContact(contact)}>
              {contact.displayName} ({contact.email})
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

### 2. **Voice Command Processing**
```javascript
// In voice command handler
const processVoiceCommand = async (command) => {
  // Extract contact names from command
  const contactNames = extractContactNames(command);
  
  for (const name of contactNames) {
    const contacts = await searchContacts(name);
    if (contacts.length > 0) {
      // Replace name with actual contact info
      command = command.replace(name, contacts[0].emailAddresses[0].value);
    }
  }
  
  return command;
};
```

### 3. **Contact Lookup Component**
```javascript
const ContactLookup = ({ onContactSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  
  useEffect(() => {
    const searchContacts = async () => {
      if (query.length >= 2) {
        const response = await fetch('/api/contacts/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: query,
            limit: 10
          })
        });
        
        const result = await response.json();
        setResults(result.success ? result.contacts : []);
      }
    };
    
    const debouncedSearch = debounce(searchContacts, 300);
    debouncedSearch();
  }, [query]);
  
  return (
    <div>
      <input 
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search contacts..."
      />
      <div className="results">
        {results.map(contact => (
          <div 
            key={contact.identifier}
            onClick={() => onContactSelect(contact)}
            className="contact-item"
          >
            <div className="name">
              {contact.firstName} {contact.lastName}
            </div>
            <div className="email">
              {contact.emailAddresses[0]?.value}
            </div>
            <div className="phone">
              {contact.phoneNumbers[0]?.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

## Best Practices

### 1. **Caching**
```javascript
// Cache contact search results to avoid repeated API calls
const contactCache = new Map();

const getCachedContacts = async (query) => {
  if (contactCache.has(query)) {
    return contactCache.get(query);
  }
  
  const result = await searchContacts(query);
  contactCache.set(query, result);
  
  // Clear cache after 5 minutes
  setTimeout(() => contactCache.delete(query), 5 * 60 * 1000);
  
  return result;
};
```

### 2. **Error Handling**
```javascript
const safeContactSearch = async (query) => {
  try {
    const response = await fetch('/api/contacts/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit: 10 })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const result = await response.json();
    return result.success ? result.contacts : [];
  } catch (error) {
    console.error('Contact search failed:', error);
    return []; // Graceful fallback
  }
};
```

### 3. **Debouncing**
```javascript
// Prevent excessive API calls during typing
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};
```

## Common Use Cases Summary

| Use Case | Endpoint | When to Use |
|----------|----------|-------------|
| **Email Resolution** | `/api/contacts/search` | User mentions name, need email |
| **Contact Validation** | `/api/contacts/search` | Verify contact exists before action |
| **Smart Suggestions** | `/api/contacts/search` | Auto-complete during typing |
| **Contact Details** | `/api/contacts/search` | Show full contact information |
| **Voice Enhancement** | `/api/contacts/search` | Resolve names in voice commands |
| **Statistics** | `/api/contacts/stats` | Show contact database overview |
| **Filtered Lists** | `/api/contacts` | Get contacts with specific criteria |

## Performance Considerations

1. **Limit Results**: Always use appropriate `limit` parameters
2. **Cache Results**: Cache frequently accessed contacts
3. **Debounce Input**: Prevent excessive API calls during typing
4. **Error Handling**: Graceful fallbacks when contacts API is unavailable
5. **Progressive Loading**: Load contacts as needed, not all at once

## Security Notes

- Contacts data is read-only from the user's MacBook
- No contact data is stored on the server
- All contact access requires user permission
- API endpoints are local to the user's machine

This integration guide provides the frontend team with clear patterns and examples for effectively using the contacts API to enhance the user experience in Iris.
