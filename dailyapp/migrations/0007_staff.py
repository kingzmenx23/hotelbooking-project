from django.db import migrations, models


def create_default_staff(apps, schema_editor):
    Staff = apps.get_model('dailyapp', 'Staff')
    Staff.objects.bulk_create([
        Staff(name='Maison Admin', username='admin', password='admin123', role='admin'),
        Staff(name='Maison Staff', username='staff', password='staff123', role='staff'),
    ])


class Migration(migrations.Migration):
    dependencies = [('dailyapp', '0006_booking')]
    operations = [
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('username', models.CharField(max_length=50, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('role', models.CharField(choices=[('admin','Admin'),('staff','Staff')], default='staff', max_length=10)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.RunPython(create_default_staff, migrations.RunPython.noop),
    ]
