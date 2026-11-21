#Wrist
WRIST_TYPING_S = 20      #continuous typing starts
#ref: Mclean. 20 minutes take a rest
WRIST_TYPING_FULL = 60
WRIST_WORK_S = 20       #continuous work starts
WRIST_WORK_FULL = 60
WRIST_TYPING_WEIGHT = 0.6
WRIST_WORK_WEIGHT = 0.4


#Eye
#Ref: Patel, Osha 
EYE_BLINK_DROP_S = 0.0   # blink rate decrease rate relative to normal
EYE_BLINK_DROP_FULL = 0.6    
EYE_BLINK_WEIGHT = 0.5      #highest weight for blink
EYE_LOOKAWAY_S = 20      #Look away for each 20 minutes
EYE_LOOKAWAY_FULL = 40
EYE_LOOKAWAY_WEIGHT = 0.3
EYE_DISTANCE_S = 50      # >= 50cm fine
EYE_DISTANCE_FULL = 35       # <=35cm bad
EYE_DISTANCE_WEIGHT = 0.2

#Postural
#ref: Hansraj
NECK_FORCE_TABLE = [(0, 12), (15, 27), (30, 40), (45, 49), (60, 60)] 
# look down angle corresponds to force
NECK_FORCE_S = 12        # 0°
NECK_FORCE_FULL = 49         # 45°
NECK_FORCE_WEIGHT = 0.7
NECK_SITTING_S = 30      # continuous sitting time
NECK_SITTING_FULL = 60
NECK_SITTING_WEIGHT = 0.3

#Mental
MIND_SLOW_S = 0.0        # inter-key 0% slower than normal
MIND_SLOW_FULL = 0.066       #after 2 hours typing
MIND_SLOW_WEIGHT = 0.5
MIND_BACKSPACE_S = 0.0   # backspace rate higher than normal
MIND_BACKSPACE_FULL = 0.29   # after 2 hours typing
MIND_BACKSPACE_WEIGHT = 0.5

# Time rules 
TYPING_PAUSE_S = 30          # >30s, resets typing timer
BREAK_S = 5 * 60             # >=5m, resets working timer
LOOKAWAY_S = 20              # >=20s resets look away
BASELINE = 10        # frist 10 min used to calculate normal behaviors

#Score
# Demo: 1 real second counts as TIME_SCALE seconds (set by `--demo`), so 20-minute thresholds show up in ~40 s
TIME_SCALE = 1.0
RISE_MINUTES = 10            # 10 minutes to reach the target
FALL_MINUTES = 3             # 3 minutes to cool down
AVERAGE_WEIGHT = 0.6        
MAX_WEIGHT = 0.4
# Toal Score= 0.6* average of 4 parts + 0.4 * worst part 
LEVEL_MODERATE = 40          # <40 low
LEVEL_HIGH = 70              # 40–69 moderate
LEVEL_CRITICAL = 85          # 70–84 high, >=85 critical

#Alert
ALERT_ON = 70                # score >=70
ALERT_SUSTAIN_S = 5 * 60     # last for 5 minutes
ALERT_IDLE_S = 3             # idle>=3
ALERT_MAX_WAIT = 10 * 60   # maximum wait time
ALERT_COOLDOWN_S = 20 * 60   # alert at most per 2o min
ALERT_RESET = 55             # after decrease to 55, allow alert again

ADVICE = {
    "ocular": "Look at something away for 20 seconds.",            
    "postural": "Sit up and raise your screen to eye level.",    
    "upper_extremity": "Stretch your wrists.",
    "cognitive": "Step away from the computer for 5 minutes.",   
}
