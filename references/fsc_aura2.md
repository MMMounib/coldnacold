# Analyse de fsc_aura2.pcf

12 systèmes, dont 4 racines.

## enfant `[99]_akuma4`
- matériau `particles\ins_debris.vmt` · max 80 · émission 80.0 /s, durée 0.0 · pic estimé ~80
- vie None · rayon (5.0, 6.0) · couleur [(88, 0, 186, 255), (30, 0, 107, 255)] · alpha None
- position : Position Modify Offset Random {'offset in local space 0/1': True, 'offset max': (0.0, 0.0, 3.0), 'offset min': (0.0, 0.0, 3.0), 'control_point_number': 0}
- position : Position Modify Warp Random {'warp min': (1.0, 1.0, 1.3), 'warp max': (0.5, 0.5, 1.0)}
- position : Position Within Sphere Random {'speed_max': 5.0, 'speed_min': 3.0, 'control_point_number': 0, 'distance_bias': (1.0, 1.0, 0.0), 'distance_max': 80.0, 'distance_min': 0.0}
- mouvement : Rotation Yaw Flip Random {'flip percentage': 0.5}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_initial': 0.0, 'rotation_offset_min': 0.0, 'rotation_offset_max': 360.0, 'rotation_random_exponent': 1.0}
- mouvement : gravité (0.0, 0.0, 1.0) traînée 0.0
- mouvement : Oscillate Scalar {'oscillation start phase': 0.5, 'oscillation multiplier': 2.0, 'start/end proportional': True, 'end time max': 1.0, 'end time min': 1.0, 'start time max': 0.0, 'start time min': 0.0, 'proportional 0/1': True, 'oscillation frequency max': 0.4, 'oscillation frequency min': 0.2, 'oscillation rate max': 15.0, 'oscillation rate min': 10.0, 'oscillation field': 3}
- mouvement : VERROU Movement Lock to Control Point {'control_point_number': 0, 'start_fadeout_min': 1.0, 'start_fadeout_max': 1.0, 'start_fadeout_exponent': 1.0, 'end_fadeout_min': 1.0, 'end_fadeout_max': 1.0, 'end_fadeout_exponent': 1.0, 'distance fade range': 0.0, 'lock rotation': True}
- aspect : Alpha Fade and Decay {'start_alpha': 1.0, 'end_alpha': 0.0, 'start_fade_in_time': 0.0, 'end_fade_in_time': 0.75, 'start_fade_out_time': 0.75, 'end_fade_out_time': 1.0}
- aspect : Alpha Fade In Random {'proportional 0/1': True, 'fade in time exponent': 1.0, 'fade in time max': 0.15, 'fade in time min': 0.15}
- aspect : rendu render_animated_sprites {'use animation rate as fps': False, 'second sequence animation rate': 0.0, 'orientation control point': 0, 'orientation_type': 2, 'animation_fit_lifetime': False, 'animation rate': 0.8}
- aspect : rendu render_animated_sprites {'use animation rate as fps': False, 'second sequence animation rate': 0.0, 'orientation control point': -1, 'orientation_type': 0, 'animation_fit_lifetime': True, 'animation rate': 0.8}

## enfant `[99]_akuma5`
- matériau `particle\impact\fleks5_add.vmt` · max 125 · émission 124.0 /s, durée 0.0 · pic estimé ~124
- vie None · rayon (1.0, 1.0) · couleur [(180, 0, 255, 255), (36, 0, 221, 255)] · alpha None
- position : Position Modify Offset Random {'offset in local space 0/1': True, 'offset max': (0.0, 0.0, 55.0), 'offset min': (0.0, 0.0, 0.0), 'control_point_number': 0}
- position : Position Modify Warp Random {'warp min': (0.0, 0.0, 0.0), 'warp max': (1.0, 1.0, 1.0)}
- position : Position Within Sphere Random {'speed_max': 6.0, 'speed_min': 3.0, 'control_point_number': 0, 'distance_bias': (1.0, 1.0, 1.0), 'distance_max': 25.0, 'distance_min': 25.0}
- mouvement : Rotation Yaw Flip Random {'flip percentage': 0.5}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_initial': 0.0, 'rotation_offset_min': 0.0, 'rotation_offset_max': 360.0, 'rotation_random_exponent': 1.0}
- mouvement : gravité (0.0, 0.0, 1.0) traînée 0.0
- mouvement : VERROU Movement Lock to Control Point {'lock rotation': True, 'distance fade range': 0.0, 'end_fadeout_exponent': 1.0, 'end_fadeout_max': 1.0, 'end_fadeout_min': 1.0, 'start_fadeout_exponent': 1.0, 'start_fadeout_max': 1.0, 'start_fadeout_min': 1.0, 'control_point_number': 0}
- mouvement : Oscillate Scalar {'oscillation field': 3, 'oscillation rate min': 3.0, 'oscillation rate max': 4.0, 'oscillation frequency min': 0.3, 'oscillation frequency max': 0.5, 'proportional 0/1': True, 'start time min': 0.0, 'start time max': 0.0, 'end time min': 1.0, 'end time max': 1.0, 'start/end proportional': True, 'oscillation multiplier': 2.0, 'oscillation start phase': 0.5}
- mouvement : random force {'max force': (15.0, 15.0, 15.0), 'min force': (-15.0, -15.0, -15.0)}
- mouvement : twist around axis {'amount of force': 64.0, 'twist axis': (0.0, 0.0, 1.0), 'object local space axis 0/1': False}
- aspect : Alpha Fade and Decay {'start_alpha': 1.0, 'end_alpha': 0.0, 'start_fade_in_time': 0.0, 'end_fade_in_time': 0.75, 'start_fade_out_time': 0.75, 'end_fade_out_time': 1.0}
- aspect : Alpha Fade In Random {'proportional 0/1': True, 'fade in time exponent': 1.0, 'fade in time max': 0.15, 'fade in time min': 0.15}
- aspect : rendu render_animated_sprites {'use animation rate as fps': False, 'second sequence animation rate': 0.0, 'orientation control point': -1, 'orientation_type': 0, 'animation_fit_lifetime': True, 'animation rate': 0.5}

## RACINE `eden_akuma_flame`
- matériau `1izox\foc\focfire2.vmt` · max 1000 · émission 60.0 /s, durée 0.0 · pic estimé ~60
- vie selon la séquence · rayon (12.0, 32.0) · couleur [(19, 0, 40, 255), (28, 0, 110, 255)] · alpha None
- position : Position Within Sphere Random {'distance_min': 0.0, 'distance_max': 16.0, 'distance_bias': (1.0, 1.0, 1.0), 'control_point_number': 0, 'speed_min': 32.0, 'speed_max': 64.0}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_initial': 0.0, 'rotation_offset_min': 0.0, 'rotation_offset_max': 360.0, 'rotation_random_exponent': 1.0}
- mouvement : Velocity Random {'control_point_number': 0, 'random_speed_min': 0.0, 'random_speed_max': 0.0, 'speed_in_local_coordinate_system_min': (-16.0, -16.0, -16.0), 'speed_in_local_coordinate_system_max': (16.0, 16.0, 16.0)}
- mouvement : gravité (0.0, 0.0, 32.0) traînée 0.0
- mouvement : Radius Scale {'start_time': 0.0, 'end_time': 1.0, 'radius_start_scale': 1.0, 'radius_end_scale': 2.5, 'ease_in_and_out': False, 'scale_bias': 0.5}
- mouvement : Collision via traces {'confirm collision': False, 'minimum speed to kill on collision': -1.0, 'collision mode': 0, 'amount of bounce': 0.0, 'amount of slide': 0.0, 'radius scale': 1.0, 'brush only': False, 'collision group': 'NONE', 'control point offset for fast collisions': (0.0, 0.0, 0.0), 'control point movement distance tolerance': 5.0, 'kill particle on collision': False, 'trace accuracy tolerance': 8.0}
- aspect : Alpha Fade and Decay {'start_alpha': 1.0, 'end_alpha': 0.0, 'start_fade_in_time': 0.0, 'end_fade_in_time': 0.5, 'start_fade_out_time': 0.8, 'end_fade_out_time': 1.0}
- aspect : rendu render_animated_sprites {'animation rate': 1.5, 'animation_fit_lifetime': True, 'orientation_type': 0, 'orientation control point': -1, 'second sequence animation rate': 0.0, 'use animation rate as fps': False}

## RACINE `[99]_akuma1`
- matériau `particle\dust\large_swirl_dust.vmt` · max 151 · émission 104.0 /s, durée 0.0 · pic estimé ~104
- enfants : [99]_akuma2, [99]_akuma3, [99]_akuma4, [99]_akuma5
- vie None · rayon None · couleur [(89, 5, 138, 255), (21, 0, 63, 255)] · alpha (200, 200)
- position : Position Modify Offset Random {'offset in local space 0/1': True, 'offset max': (0.0, 0.0, 55.0), 'offset min': (0.0, 0.0, 0.0), 'control_point_number': 0}
- position : Position Modify Warp Random {'warp min': (0.0, 0.0, 0.0), 'warp max': (1.0, 1.0, 1.0)}
- position : Position Within Sphere Random {'speed_max': 0.0, 'speed_min': 0.0, 'control_point_number': 0, 'distance_bias': (1.0, 1.0, 1.0), 'distance_max': 25.0, 'distance_min': 25.0}
- mouvement : Rotation Yaw Flip Random {'flip percentage': 0.5}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_initial': 0.0, 'rotation_offset_min': 0.0, 'rotation_offset_max': 360.0, 'rotation_random_exponent': 1.0}
- mouvement : gravité (0.0, 0.0, 0.0) traînée 0.0
- mouvement : Oscillate Scalar {'oscillation start phase': 0.5, 'oscillation multiplier': 2.0, 'start/end proportional': True, 'end time max': 1.0, 'end time min': 1.0, 'start time max': 0.0, 'start time min': 0.0, 'proportional 0/1': True, 'oscillation frequency max': 0.3, 'oscillation frequency min': 0.2, 'oscillation rate max': 30.0, 'oscillation rate min': 30.0, 'oscillation field': 3}
- mouvement : VERROU Movement Lock to Control Point {'control_point_number': 0, 'start_fadeout_min': 1.0, 'start_fadeout_max': 1.0, 'start_fadeout_exponent': 1.0, 'end_fadeout_min': 1.0, 'end_fadeout_max': 1.0, 'end_fadeout_exponent': 1.0, 'distance fade range': 0.0, 'lock rotation': True}
- aspect : Alpha Fade and Decay {'start_alpha': 1.0, 'end_alpha': 0.0, 'start_fade_in_time': 0.0, 'end_fade_in_time': 0.75, 'start_fade_out_time': 0.75, 'end_fade_out_time': 1.0}
- aspect : Alpha Fade In Random {'proportional 0/1': True, 'fade in time exponent': 1.0, 'fade in time max': 0.15, 'fade in time min': 0.15}
- aspect : rendu render_animated_sprites {'use animation rate as fps': False, 'second sequence animation rate': 0.0, 'orientation control point': -1, 'orientation_type': 0, 'animation_fit_lifetime': True, 'animation rate': 0.5}

## enfant `[99]_akuma3`
- matériau `particles\ins_debris.vmt` · max 151 · émission 160.0 /s, durée 0.0 · pic estimé ~160
- vie None · rayon None · couleur [(92, 15, 196, 255), (28, 0, 74, 255)] · alpha None
- position : Position Modify Offset Random {'control_point_number': 0, 'offset min': (0.0, 0.0, 0.0), 'offset max': (0.0, 0.0, 55.0), 'offset in local space 0/1': True}
- position : Position Modify Warp Random {'warp max': (1.0, 1.0, 1.0), 'warp min': (0.0, 0.0, 0.0)}
- position : Position Within Sphere Random {'distance_min': 25.0, 'distance_max': 25.0, 'distance_bias': (1.0, 1.0, 1.0), 'control_point_number': 0, 'speed_min': 0.0, 'speed_max': 0.0}
- mouvement : Rotation Yaw Flip Random {'flip percentage': 0.5}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_random_exponent': 1.0, 'rotation_offset_max': 360.0, 'rotation_offset_min': 0.0, 'rotation_initial': 0.0}
- mouvement : gravité (0.0, 0.0, 0.0) traînée 0.0
- mouvement : Oscillate Scalar {'oscillation field': 3, 'oscillation rate min': 12.0, 'oscillation rate max': 15.0, 'oscillation frequency min': 0.2, 'oscillation frequency max': 0.3, 'proportional 0/1': True, 'start time min': 0.0, 'start time max': 0.0, 'end time min': 1.0, 'end time max': 1.0, 'start/end proportional': True, 'oscillation multiplier': 2.0, 'oscillation start phase': 0.5}
- mouvement : VERROU Movement Lock to Control Point {'control_point_number': 0, 'start_fadeout_min': 1.0, 'start_fadeout_max': 1.0, 'start_fadeout_exponent': 1.0, 'end_fadeout_min': 1.0, 'end_fadeout_max': 1.0, 'end_fadeout_exponent': 1.0, 'distance fade range': 0.0, 'lock rotation': True}
- mouvement : random force {'min force': (-15.0, -15.0, -15.0), 'max force': (15.0, 15.0, 15.0)}
- aspect : Alpha Fade and Decay {'end_fade_out_time': 1.0, 'start_fade_out_time': 0.75, 'end_fade_in_time': 0.75, 'start_fade_in_time': 0.0, 'end_alpha': 0.0, 'start_alpha': 1.0}
- aspect : Alpha Fade In Random {'fade in time min': 0.15, 'fade in time max': 0.15, 'fade in time exponent': 1.0, 'proportional 0/1': True}
- aspect : rendu render_animated_sprites {'animation rate': 0.5, 'animation_fit_lifetime': True, 'orientation_type': 0, 'orientation control point': -1, 'second sequence animation rate': 0.0, 'use animation rate as fps': False}

## enfant `[99]_akuma2`
- matériau `particle\dust\large_swirl_dust.vmt` · max 151 · émission 70.0 /s, durée 0.0 · pic estimé ~70
- vie None · rayon (5.0, 10.0) · couleur [(74, 0, 142, 255), (126, 0, 255, 255)] · alpha (200, 200)
- position : Position Modify Offset Random {'control_point_number': 0, 'offset min': (0.0, 0.0, 3.0), 'offset max': (0.0, 0.0, 3.0), 'offset in local space 0/1': True}
- position : Position Modify Warp Random {'warp max': (0.5, 0.5, 1.0), 'warp min': (1.0, 1.0, 1.3)}
- position : Position Within Sphere Random {'distance_min': 0.0, 'distance_max': 80.0, 'distance_bias': (1.0, 1.0, 0.0), 'control_point_number': 0, 'speed_min': 3.0, 'speed_max': 5.0}
- mouvement : Rotation Yaw Flip Random {'flip percentage': 0.5}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_random_exponent': 1.0, 'rotation_offset_max': 360.0, 'rotation_offset_min': 0.0, 'rotation_initial': 0.0}
- mouvement : gravité (0.0, 0.0, 1.0) traînée 0.0
- mouvement : Oscillate Scalar {'oscillation field': 3, 'oscillation rate min': 20.0, 'oscillation rate max': 20.0, 'oscillation frequency min': 0.2, 'oscillation frequency max': 0.4, 'proportional 0/1': True, 'start time min': 0.0, 'start time max': 0.0, 'end time min': 1.0, 'end time max': 1.0, 'start/end proportional': True, 'oscillation multiplier': 2.0, 'oscillation start phase': 0.5}
- mouvement : VERROU Movement Lock to Control Point {'control_point_number': 0, 'start_fadeout_min': 1.0, 'start_fadeout_max': 1.0, 'start_fadeout_exponent': 1.0, 'end_fadeout_min': 1.0, 'end_fadeout_max': 1.0, 'end_fadeout_exponent': 1.0, 'distance fade range': 0.0, 'lock rotation': True}
- aspect : Alpha Fade and Decay {'end_fade_out_time': 1.0, 'start_fade_out_time': 0.75, 'end_fade_in_time': 0.75, 'start_fade_in_time': 0.0, 'end_alpha': 0.0, 'start_alpha': 1.0}
- aspect : Alpha Fade In Random {'fade in time min': 0.15, 'fade in time max': 0.15, 'fade in time exponent': 1.0, 'proportional 0/1': True}
- aspect : rendu render_animated_sprites {'animation rate': 0.8, 'animation_fit_lifetime': False, 'orientation_type': 2, 'orientation control point': 0, 'second sequence animation rate': 0.0, 'use animation rate as fps': False}
- aspect : rendu render_animated_sprites {'animation rate': 0.8, 'animation_fit_lifetime': True, 'orientation_type': 0, 'orientation control point': -1, 'second sequence animation rate': 0.0, 'use animation rate as fps': False}

## enfant `[8]_amaterasu_armor3`
- matériau `1izox\foc\focfire2.vmt` · max 84 · émission 84.0 /s, durée 0.0 · pic estimé ~84
- vie None · rayon None · couleur [(14, 14, 14, 255), (0, 0, 0, 255)] · alpha None
- position : Position on Model Random {'control_point_number': 0, 'model hitbox scale': 1.0, 'direction bias': (0.0, 0.0, 0.0), 'hitbox set': 'effects'}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_random_exponent': 1.0, 'rotation_offset_max': 360.0, 'rotation_offset_min': 0.0, 'rotation_initial': 0.0}
- mouvement : Rotation Yaw Flip Random {'flip percentage': 0.5}
- mouvement : Velocity Random {'control_point_number': 0, 'random_speed_min': -15.0, 'random_speed_max': 15.0, 'speed_in_local_coordinate_system_min': (0.0, 0.0, 0.0), 'speed_in_local_coordinate_system_max': (0.0, 0.0, 0.0)}
- mouvement : gravité (0.0, 0.0, 5.0) traînée 0.0
- mouvement : Rotation Spin Roll {'spin_rate_min': 0, 'spin_stop_time': 0.0, 'spin_rate_degrees': 5}
- mouvement : Noise Scalar {'additive': False, 'output maximum': 20.0, 'output minimum': -5.0, 'output field': 3, 'noise coordinate scale': 1.0}
- mouvement : VERROU Movement Lock to Bone {'hitbox set': 'effects', 'lifetime fade end': 0.7, 'lifetime fade start': 0.7, 'control_point_number': 0}
- aspect : Alpha Fade and Decay {'start_alpha': 1.0, 'end_alpha': 0.0, 'start_fade_in_time': 0.0, 'end_fade_in_time': 0.65, 'start_fade_out_time': 0.65, 'end_fade_out_time': 1.0}
- aspect : Alpha Fade In Random {'fade in time min': 0.25, 'fade in time max': 0.25, 'fade in time exponent': 1.0, 'proportional 0/1': True}
- aspect : rendu render_animated_sprites {'use animation rate as fps': False, 'second sequence animation rate': 0.0, 'orientation control point': -1, 'orientation_type': 0, 'animation_fit_lifetime': True, 'animation rate': 0.9}

## RACINE `[8]_amaterasu_armor`
- matériau `effects\sc_hardglow.vmt` · max 64 · émission 50.0 /s, durée 0.0 · pic estimé ~50
- enfants : [8]_amaterasu_armor2, [8]_amaterasu_armor3
- vie None · rayon None · couleur [(0, 0, 0, 255), (51, 51, 51, 255)] · alpha (10, 10)
- position : Position on Model Random {'hitbox set': 'effects', 'direction bias': (0.0, 0.0, 0.0), 'model hitbox scale': 1.0, 'control_point_number': 0}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_initial': 0.0, 'rotation_offset_min': 0.0, 'rotation_offset_max': 360.0, 'rotation_random_exponent': 1.0}
- mouvement : Rotation Yaw Flip Random {'flip percentage': 0.5}
- mouvement : Velocity Random {'speed_in_local_coordinate_system_max': (0.0, 0.0, 0.0), 'speed_in_local_coordinate_system_min': (0.0, 0.0, 0.0), 'random_speed_max': 15.0, 'random_speed_min': -15.0, 'control_point_number': 0}
- mouvement : gravité (0.0, 0.0, 5.0) traînée 0.0
- mouvement : Rotation Spin Roll {'spin_rate_degrees': 5, 'spin_stop_time': 0.0, 'spin_rate_min': 0}
- mouvement : Noise Scalar {'additive': False, 'noise coordinate scale': 0.1, 'output field': 3, 'output minimum': 30.0, 'output maximum': 30.0}
- mouvement : VERROU Movement Lock to Bone {'control_point_number': 0, 'lifetime fade start': 0.8, 'lifetime fade end': 0.8, 'hitbox set': 'effects'}
- aspect : Alpha Fade and Decay {'end_fade_out_time': 1.0, 'start_fade_out_time': 0.65, 'end_fade_in_time': 0.65, 'start_fade_in_time': 0.0, 'end_alpha': 0.0, 'start_alpha': 1.0}
- aspect : Alpha Fade In Random {'proportional 0/1': True, 'fade in time exponent': 1.0, 'fade in time max': 0.25, 'fade in time min': 0.25}
- aspect : rendu render_animated_sprites {'animation rate': 0.9, 'animation_fit_lifetime': True, 'orientation_type': 0, 'orientation control point': -1, 'second sequence animation rate': 0.0, 'use animation rate as fps': False}

## enfant `[8]_amaterasu_armor2`
- matériau `1izox\foc\focfire2.vmt` · max 70 · émission 70.0 /s, durée 0.0 · pic estimé ~70
- vie None · rayon None · couleur [(15, 15, 15, 255), (0, 0, 0, 255)] · alpha None
- position : Position on Model Random {'control_point_number': 0, 'model hitbox scale': 1.0, 'direction bias': (0.0, 0.0, 0.0), 'hitbox set': 'effects'}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_random_exponent': 1.0, 'rotation_offset_max': 360.0, 'rotation_offset_min': 0.0, 'rotation_initial': 0.0}
- mouvement : Rotation Yaw Flip Random {'flip percentage': 0.5}
- mouvement : Velocity Random {'control_point_number': 0, 'random_speed_min': -15.0, 'random_speed_max': 15.0, 'speed_in_local_coordinate_system_min': (0.0, 0.0, 0.0), 'speed_in_local_coordinate_system_max': (0.0, 0.0, 0.0)}
- mouvement : gravité (0.0, 0.0, 5.0) traînée 0.0
- mouvement : Rotation Spin Roll {'spin_rate_min': 0, 'spin_stop_time': 0.0, 'spin_rate_degrees': 5}
- mouvement : Noise Scalar {'additive': False, 'output maximum': 20.0, 'output minimum': -5.0, 'output field': 3, 'noise coordinate scale': 1.0}
- mouvement : VERROU Movement Lock to Bone {'hitbox set': 'effects', 'lifetime fade end': 0.7, 'lifetime fade start': 0.7, 'control_point_number': 0}
- aspect : Alpha Fade and Decay {'start_alpha': 1.0, 'end_alpha': 0.0, 'start_fade_in_time': 0.0, 'end_fade_in_time': 0.65, 'start_fade_out_time': 0.65, 'end_fade_out_time': 1.0}
- aspect : Alpha Fade In Random {'fade in time min': 0.25, 'fade in time max': 0.25, 'fade in time exponent': 1.0, 'proportional 0/1': True}
- aspect : rendu render_animated_sprites {'use animation rate as fps': False, 'second sequence animation rate': 0.0, 'orientation control point': -1, 'orientation_type': 0, 'animation_fit_lifetime': True, 'animation rate': 0.9}

## enfant `[0]_blackfire_armor3`
- matériau `1izox\feu.vmt` · max 101 · émission 70.0 /s, durée 5.0 · pic estimé ~63
- vie (0.91, 0.91) · rayon (1.0, 3.0) · couleur [(0, 0, 0, 255), (8, 8, 8, 255)] · alpha (50, 200)
- position : Position Within Sphere Random {'distance_min': 0.0, 'distance_max': 0.0, 'distance_bias': (1.0, 1.0, 1.0), 'control_point_number': 0, 'speed_min': 60.0, 'speed_max': 80.0}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_initial': 0.0, 'rotation_offset_min': 0.0, 'rotation_offset_max': 360.0, 'rotation_random_exponent': 1.0}
- mouvement : gravité (0.0, 0.0, 0.0) traînée 0.0
- mouvement : VERROU Movement Lock to Control Point {'control_point_number': 0, 'start_fadeout_min': 1.0, 'start_fadeout_max': 1.0, 'start_fadeout_exponent': 1.0, 'end_fadeout_min': 1.0, 'end_fadeout_max': 1.0, 'end_fadeout_exponent': 1.0, 'distance fade range': 0.0, 'lock rotation': False}
- mouvement : Radius Scale {'start_time': 0.0, 'end_time': 1.0, 'radius_start_scale': 2.0, 'radius_end_scale': 12.0, 'ease_in_and_out': False, 'scale_bias': 0.5}
- mouvement : Set Control Point Positions {'control point to offset positions from': 0, 'set positions in world space': False, 'fourth control point location': (0.0, -18.0, 0.0), 'fourth control point parent': 0, 'fourth control point number': 4, 'third control point location': (-18.0, 0.0, 0.0), 'third control point parent': 0, 'third control point number': 3, 'second control point location': (0.0, 18.0, 0.0), 'second control point parent': 0, 'second control point number': 2, 'first control point location': (0.0, 0.0, 30.0), 'first control point parent': 0, 'first control point number': 1}
- mouvement : Pull towards control point {'control point number': 1, 'falloff power': 0.0, 'amount of force': 350.0}
- aspect : Alpha Fade and Decay {'end_fade_out_time': 1.0, 'start_fade_out_time': 1.05, 'end_fade_in_time': 0.95, 'start_fade_in_time': 0.0, 'end_alpha': 0.0, 'start_alpha': 1.0}
- aspect : Alpha Fade In Random {'fade in time min': 0.3, 'fade in time max': 0.3, 'fade in time exponent': 1.0, 'proportional 0/1': True}
- aspect : rendu render_animated_sprites {'animation rate': 1.0, 'animation_fit_lifetime': True, 'orientation_type': 0, 'orientation control point': -1, 'second sequence animation rate': 0.0, 'use animation rate as fps': False}

## enfant `[0]_blackfire_armor2`
- matériau `pfx\fire_basic_nocolor_v2.vmt` · max 1000 · émission 104.0 /s, durée 0.0 · pic estimé ~104
- vie None · rayon None · couleur [(17, 17, 17, 255), (0, 0, 0, 255)] · alpha None
- position : Position on Model Random {'control_point_number': 0, 'model hitbox scale': 1.0, 'direction bias': (0.0, 0.0, 0.0), 'hitbox set': 'effects'}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_initial': 0.0, 'rotation_offset_min': 0.0, 'rotation_offset_max': 360.0, 'rotation_random_exponent': 1.0}
- mouvement : Velocity Random {'speed_in_local_coordinate_system_max': (0.0, 0.0, 0.0), 'speed_in_local_coordinate_system_min': (0.0, 0.0, 0.0), 'random_speed_max': 10.0, 'random_speed_min': -10.0, 'control_point_number': 0}
- mouvement : gravité (0.0, 0.0, 40.0) traînée 0.0
- mouvement : Oscillate Scalar {'oscillation start phase': 0.5, 'oscillation multiplier': 2.0, 'start/end proportional': True, 'end time max': 1.0, 'end time min': 1.0, 'start time max': 0.0, 'start time min': 0.0, 'proportional 0/1': True, 'oscillation frequency max': 0.45, 'oscillation frequency min': 0.25, 'oscillation rate max': 25.0, 'oscillation rate min': 20.0, 'oscillation field': 3}
- mouvement : VERROU Movement Lock to Bone {'control_point_number': 0, 'lifetime fade start': 0.7, 'lifetime fade end': 0.7, 'hitbox set': 'effects'}
- aspect : Alpha Fade and Decay {'start_alpha': 1.0, 'end_alpha': 0.0, 'start_fade_in_time': 0.0, 'end_fade_in_time': 0.5, 'start_fade_out_time': 0.5, 'end_fade_out_time': 1.0}
- aspect : Alpha Fade In Random {'fade in time min': 0.25, 'fade in time max': 0.25, 'fade in time exponent': 1.0, 'proportional 0/1': True}
- aspect : rendu render_animated_sprites {'animation rate': 0.9, 'animation_fit_lifetime': False, 'orientation_type': 0, 'orientation control point': -1, 'second sequence animation rate': 0.0, 'use animation rate as fps': False}

## RACINE `[0]_blackfire_armor1`
- matériau `effects\horizontalglow.vmt` · max 1000 · émission 104.0 /s, durée 0.0 · pic estimé ~104
- enfants : [0]_blackfire_armor3, [0]_blackfire_armor2
- vie None · rayon None · couleur [(8, 8, 8, 255), (18, 18, 18, 255)] · alpha (100, 100)
- position : Position on Model Random {'hitbox set': 'effects', 'direction bias': (0.0, 0.0, 0.0), 'model hitbox scale': 1.0, 'control_point_number': 0}
- mouvement : Rotation Random {'randomly_flip_direction': True, 'rotation_random_exponent': 1.0, 'rotation_offset_max': 90.0, 'rotation_offset_min': 90.0, 'rotation_initial': 0.0}
- mouvement : gravité (0.0, 0.0, 40.0) traînée 0.0
- mouvement : Oscillate Scalar {'oscillation field': 3, 'oscillation rate min': 30.0, 'oscillation rate max': 40.0, 'oscillation frequency min': 0.1, 'oscillation frequency max': 0.2, 'proportional 0/1': True, 'start time min': 0.0, 'start time max': 0.0, 'end time min': 1.0, 'end time max': 1.0, 'start/end proportional': True, 'oscillation multiplier': 2.0, 'oscillation start phase': 0.5}
- mouvement : VERROU Movement Lock to Bone {'control_point_number': 0, 'lifetime fade start': 0.7, 'lifetime fade end': 0.7, 'hitbox set': 'effects'}
- aspect : Alpha Fade and Decay {'end_fade_out_time': 1.0, 'start_fade_out_time': 0.5, 'end_fade_in_time': 0.5, 'start_fade_in_time': 0.0, 'end_alpha': 0.0, 'start_alpha': 1.0}
- aspect : Alpha Fade In Random {'proportional 0/1': True, 'fade in time exponent': 1.0, 'fade in time max': 0.25, 'fade in time min': 0.25}
- aspect : rendu render_animated_sprites {'animation rate': 0.1, 'animation_fit_lifetime': False, 'orientation_type': 0, 'orientation control point': -1, 'second sequence animation rate': 0.0, 'use animation rate as fps': False}

