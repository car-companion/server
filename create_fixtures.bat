@echo off
rem Run from inside poetry shell

rem ====================
rem # Vehicle fixtures #
rem ====================
set "vehicle_ownership_vins=YV1MS672482401129 5UXKR2C58F0801672"
set "vehicle_ownership_usernames=testuser testuser2"
set "vehicle_ownership_file=vehicle\fixtures\fixture_ownership.json"
set "vehicle_ownership_vehicles_temp=vehicle\fixtures\_fixture_vehicles.json"
set "vehicle_ownership_users_temp=vehicle\fixtures\_fixture_usernames.json"

rem Convert usernames to pks since dump_object only accepts primary keys of models
FOR /F "tokens=*" %%g IN (
	'python manage.py shell -c "from django.contrib.auth.models import User; import shlex; print(' '.join(map(str, User.objects.filter( username__in=shlex.split(\"%vehicle_ownership_usernames%\") ).values_list(\"pk\", flat=True) )))"'
) do set "vehicle_ownership_user_pks=%%g"

rem Dump vehicles, users (with their references) and then merge them into a single fixture
python manage.py dump_object vehicle.Vehicle %vehicle_ownership_vins% > "%vehicle_ownership_vehicles_temp%"
python manage.py dump_object auth.User %vehicle_ownership_user_pks% > "%vehicle_ownership_users_temp%"
python manage.py merge_fixtures "%vehicle_ownership_vehicles_temp%" "%vehicle_ownership_users_temp%" > "%vehicle_ownership_file%"
del "%vehicle_ownership_vehicles_temp%"
del "%vehicle_ownership_users_temp%"
