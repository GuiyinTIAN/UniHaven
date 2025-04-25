import uuid
from django.core.management.base import BaseCommand
from accommodation.models import University, UniversityAPIKey

class Command(BaseCommand):
    help = '为大学系统生成API密钥'

    def add_arguments(self, parser):
        parser.add_argument('--university', type=str, help='大学代码，例如HKU', required=False)
        parser.add_argument('--all', action='store_true', help='为所有大学生成API密钥')
        parser.add_argument('--regenerate', action='store_true', help='重新生成已存在的API密钥')

    def handle(self, *args, **options):
        university_code = options.get('university')
        regenerate = options.get('regenerate')
        
        if options.get('all'):
            universities = University.objects.all()
        elif university_code:
            try:
                universities = [University.objects.get(code=university_code)]
            except University.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"The university with the code '{university_code}' was not found"))
                return
        else:
            self.stdout.write(self.style.ERROR("需要指定--university或--all参数"))
            return
            
        for university in universities:
            try:
                api_key, created = UniversityAPIKey.objects.get_or_create(
                    university=university,
                    defaults={'key': str(uuid.uuid4()).replace('-', '')}
                )
                
                if not created and regenerate:
                    api_key.key = str(uuid.uuid4()).replace('-', '')
                    api_key.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"已为{university.name} ({university.code})重新生成API密钥: {api_key.key}"
                    ))
                elif created:
                    self.stdout.write(self.style.SUCCESS(
                        f"已为{university.name} ({university.code})生成API密钥: {api_key.key}"
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"{university.name} ({university.code})已有API密钥: {api_key.key}"
                    ))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"为{university.name}生成API密钥时出错: {str(e)}"))
