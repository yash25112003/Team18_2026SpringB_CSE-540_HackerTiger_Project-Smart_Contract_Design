"""
Django Management Command for Automatic Blockchain Block Rotation
Rotates blockchain blocks every 10 minutes with new Block IDs
"""
import time
import threading
from django.core.management.base import BaseCommand
from django.utils import timezone
from deploy.services import check_and_rotate_block, get_blockchain_stats


class Command(BaseCommand):
    help = 'Automatically rotate blockchain blocks every 10 minutes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=20,  # 10 minutes in seconds
            help='Block rotation interval in seconds (default: 600 = 10 minutes)',
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as daemon (background process)',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run rotation check once and exit',
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        daemon = options['daemon']
        once = options['once']
        
        self.stdout.write(
            self.style.SUCCESS(f'🔄 Starting blockchain block rotation system')
        )
        self.stdout.write(f'⏰ Rotation interval: {interval} seconds ({interval/60:.1f} minutes)')
        
        if once:
            self.stdout.write('🔍 Running single rotation check...')
            self.rotate_once()
            return
        
        if daemon:
            self.stdout.write('👻 Running in daemon mode...')
            self.run_daemon(interval)
        else:
            self.stdout.write('🖥️ Running in foreground mode (Ctrl+C to stop)...')
            self.run_foreground(interval)
    
    def rotate_once(self):
        """Run a single rotation check"""
        try:
            stats_before = get_blockchain_stats()
            self.stdout.write(f"📊 Before rotation: {stats_before}")
            
            result = check_and_rotate_block()
            
            stats_after = get_blockchain_stats()
            self.stdout.write(f"📊 After rotation: {stats_after}")
            
            if result:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Block rotation check completed')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Block rotation check had issues')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Rotation check failed: {str(e)}')
            )
    
    def run_foreground(self, interval):
        """Run rotation in foreground with periodic updates"""
        try:
            rotation_count = 0
            start_time = timezone.now()
            
            while True:
                try:
                    self.stdout.write(f'🔄 Rotation check #{rotation_count + 1} at {timezone.now()}')
                    
                    stats_before = get_blockchain_stats()
                    result = check_and_rotate_block()
                    stats_after = get_blockchain_stats()
                    
                    if stats_after['active_block_number'] != stats_before['active_block_number']:
                        rotation_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'🆕 NEW BLOCK CREATED! Block #{stats_after["active_block_number"]} '
                                f'(ID: {stats_after["active_block_id"]})'
                            )
                        )
                    else:
                        self.stdout.write(f'⏳ Block #{stats_after["active_block_number"]} still active')
                    
                    # Show runtime stats
                    runtime = timezone.now() - start_time
                    self.stdout.write(
                        f'📈 Runtime: {runtime}, Total rotations: {rotation_count}, '
                        f'Total blocks: {stats_after["total_blocks"]}'
                    )
                    
                    self.stdout.write(f'😴 Sleeping for {interval} seconds...\n')
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    self.stdout.write('\n🛑 Received interrupt signal')
                    break
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Rotation error: {str(e)}')
                    )
                    self.stdout.write(f'⏳ Continuing in {interval} seconds...')
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stdout.write(
                self.style.SUCCESS(f'✨ Block rotation system stopped. Total rotations: {rotation_count}')
            )
    
    def run_daemon(self, interval):
        """Run rotation as background daemon"""
        def daemon_worker():
            rotation_count = 0
            while True:
                try:
                    result = check_and_rotate_block()
                    if result:
                        rotation_count += 1
                        print(f'🔄 Background rotation #{rotation_count} at {timezone.now()}')
                    time.sleep(interval)
                except Exception as e:
                    print(f'❌ Background rotation error: {str(e)}')
                    time.sleep(interval)
        
        daemon_thread = threading.Thread(target=daemon_worker, daemon=True)
        daemon_thread.start()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Daemon thread started for block rotation')
        )
        
        # Keep main thread alive
        try:
            while daemon_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write('\n🛑 Daemon stopped')
