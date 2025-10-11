"""
Notes Agent - Notes Integration

This agent handles all note-taking tasks:
1. Creating new notes
2. Searching existing notes
3. Updating and editing notes
4. Organizing notes with tags/categories
5. Converting voice to text notes

Integration Points:
- Receives task requests from vocal_core_agent
- Uses Apple Notes API or file system for note storage
- Sends status updates back to vocal_core_agent
"""

import asyncio
from typing import Dict, Any, List, Optional
from uagents import Agent, Context, Model
from pydantic import BaseModel
from datetime import datetime
import os

# Initialize the notes agent
agent = Agent(
    name="notes_agent",
    port=8003,
    seed="notes_agent_seed",
    endpoint=["http://127.0.0.1:8003/submit"]
)

# Message Models
class NotesTask(Model):
    """Notes task from vocal_core_agent"""
    intent: str
    parameters: Dict[str, Any]
    request_id: str

class NotesResponse(Model):
    """Response back to vocal_core_agent"""
    success: bool
    message: str
    note_data: Optional[Dict[str, Any]]
    request_id: str

class NoteDetails(BaseModel):
    """Note details"""
    title: str
    content: str
    tags: List[str] = []
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

@agent.on_startup
async def startup(ctx: Context):
    """Initialize notes agent"""
    ctx.logger.info("Notes Agent starting up...")
    ctx.logger.info(f"Agent address: {agent.address}")
    
    # TODO: Initialize Notes API or file system access
    # TODO: Set up note storage connection

@agent.on_message(model=NotesTask)
async def handle_notes_task(ctx: Context, sender: str, msg: NotesTask):
    """Handle notes task from vocal_core_agent"""
    ctx.logger.info(f"Received notes task: {msg.intent}")
    
    try:
        response = None
        
        if msg.intent == "create_note":
            response = await create_note(ctx, msg.parameters)
        elif msg.intent == "search_notes":
            response = await search_notes(ctx, msg.parameters)
        elif msg.intent == "update_note":
            response = await update_note(ctx, msg.parameters)
        elif msg.intent == "delete_note":
            response = await delete_note(ctx, msg.parameters)
        elif msg.intent == "list_notes":
            response = await list_recent_notes(ctx, msg.parameters)
        elif msg.intent == "organize_notes":
            response = await organize_notes(ctx, msg.parameters)
        else:
            response = NotesResponse(
                success=False,
                message=f"Unknown notes intent: {msg.intent}",
                note_data=None,
                request_id=msg.request_id
            )
        
        # Send response back to vocal_core_agent
        await ctx.send(sender, response)
        
    except Exception as e:
        ctx.logger.error(f"Error handling notes task: {e}")
        error_response = NotesResponse(
            success=False,
            message=f"Error processing notes task: {str(e)}",
            note_data=None,
            request_id=msg.request_id
        )
        await ctx.send(sender, error_response)

async def create_note(ctx: Context, parameters: Dict[str, Any]) -> NotesResponse:
    """
    Create a new note
    TODO: Implement actual Notes API call or file creation
    """
    ctx.logger.info("Creating note...")
    
    title = parameters.get("title", "New Note")
    content = parameters.get("content", "")
    tags = parameters.get("tags", [])
    
    # TODO: Create note using Apple Notes API or file system
    # TODO: Handle voice-to-text conversion if needed
    
    note_data = {
        "note_id": "mock_note_123",
        "title": title,
        "content": content,
        "created_at": datetime.now().isoformat(),
        "tags": tags
    }
    
    return NotesResponse(
        success=True,
        message=f"Note '{title}' created successfully",
        note_data=note_data,
        request_id=parameters.get("request_id", "")
    )

async def search_notes(ctx: Context, parameters: Dict[str, Any]) -> NotesResponse:
    """
    Search notes by content or tags
    TODO: Implement actual search functionality
    """
    ctx.logger.info("Searching notes...")
    
    query = parameters.get("query", "")
    
    # TODO: Search through notes content and titles
    
    search_results = [
        {"title": "Meeting Notes", "snippet": "Project discussion..."},
        {"title": "Ideas", "snippet": "New feature ideas..."}
    ]
    
    return NotesResponse(
        success=True,
        message=f"Found {len(search_results)} notes matching '{query}'",
        note_data={"results": search_results},
        request_id=parameters.get("request_id", "")
    )

async def update_note(ctx: Context, parameters: Dict[str, Any]) -> NotesResponse:
    """
    Update an existing note
    TODO: Implement actual update functionality
    """
    ctx.logger.info("Updating note...")
    
    # TODO: Find and update note
    
    return NotesResponse(
        success=True,
        message="Note updated successfully",
        note_data=None,
        request_id=parameters.get("request_id", "")
    )

async def delete_note(ctx: Context, parameters: Dict[str, Any]) -> NotesResponse:
    """
    Delete a note
    TODO: Implement actual deletion
    """
    ctx.logger.info("Deleting note...")
    
    # TODO: Find and delete note
    
    return NotesResponse(
        success=True,
        message="Note deleted successfully",
        note_data=None,
        request_id=parameters.get("request_id", "")
    )

async def list_recent_notes(ctx: Context, parameters: Dict[str, Any]) -> NotesResponse:
    """
    List recent notes
    TODO: Implement actual listing
    """
    ctx.logger.info("Listing recent notes...")
    
    limit = parameters.get("limit", 10)
    
    recent_notes = [
        {"title": "Today's Tasks", "updated": "2024-10-10"},
        {"title": "Project Ideas", "updated": "2024-10-09"},
        {"title": "Shopping List", "updated": "2024-10-08"}
    ]
    
    return NotesResponse(
        success=True,
        message=f"Found {len(recent_notes)} recent notes",
        note_data={"notes": recent_notes},
        request_id=parameters.get("request_id", "")
    )

async def organize_notes(ctx: Context, parameters: Dict[str, Any]) -> NotesResponse:
    """
    Organize notes with tags and categories
    TODO: Implement organization functionality
    """
    ctx.logger.info("Organizing notes...")
    
    # TODO: Apply tags, categories, folders
    
    return NotesResponse(
        success=True,
        message="Notes organized successfully",
        note_data=None,
        request_id=parameters.get("request_id", "")
    )

if __name__ == "__main__":
    print("Starting Notes Agent...")
    print(f"Agent will run on: {agent.address}")
    print("This agent handles:")
    print("  - Creating and editing notes")
    print("  - Searching note content")
    print("  - Organizing notes with tags")
    print("  - Voice-to-text note creation")
    
    agent.run()