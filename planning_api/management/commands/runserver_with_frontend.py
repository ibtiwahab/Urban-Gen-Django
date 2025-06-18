# planning_api/management/commands/runserver_with_frontend.py
import os
import subprocess
import webbrowser
from django.core.management.base import BaseCommand
from django.core.management.commands.runserver import Command as RunServerCommand

class Command(RunServerCommand):
    """
    Custom management command that runs Django server and optionally opens browser
    Similar to your C# Program.cs functionality
    """
    
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--open-browser',
            action='store_true',
            help='Open browser automatically',
        )
        parser.add_argument(
            '--frontend-url',
            type=str,
            default='http://localhost:5173',
            help='Frontend URL to open in browser',
        )
    
    def handle(self, *args, **options):
        if options.get('open_browser'):
            # Open browser after server starts
            server_url = f"http://{options['addrport'] or '127.0.0.1:8000'}"
            frontend_url = options.get('frontend_url')
            
            print(f"Django server starting at: {server_url}")
            if frontend_url:
                print(f"Opening frontend at: {frontend_url}")
                webbrowser.open(frontend_url)
            else:
                print(f"Opening server at: {server_url}")
                webbrowser.open(server_url)
        
        # Run the actual server
        super().handle(*args, **options)