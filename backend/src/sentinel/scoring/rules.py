# Every 5 s update once
# translate different unit of measurement into a number from 0~1
# when measurement is less than _S, consequence is 0, when it's Full. consequence is 1

#ex. WRIST_TYPING_S =20 is 0, WRIST_TYPING_FULL =60 is 1
from sentinel.scoring import config as C

def ramp(value, start, full):
    """0 below start, 1 at full, straight line in between."""
    t = (value - start) / (full - start)    #calculate a value between 0-1
    return max(0.0, min(1.0, t))    #let t be between 0~1, less than 0 return 0, larger than 1 return 1


class Rules:
    def __init__(self): #initial value, always call itself so can keep the memory
        self.work_s = 0.0            # seconds of work without a 5-min break
        self.screen_s = 0.0          # seconds without looking away for 20 s
        self.normal = None           # user's normal values, taken at minute 10, won't change later
        self.elapsed_s = 0.0         # the total programming running time
        self.parts = {"upper_extremity": 0.0, "ocular": 0.0, "postural": 0.0, "cognitive": 0.0}
        self.last_alert_s = -C.ALERT_COOLDOWN_S #assuming 20 minutes ago there's one alert, so at the beginning of the program, allows alert

    def update(self, f, dt=5.0):    #f is the packing data: keyboard, mouse and vision
        kb, vis = f.keyboard, f.vision
        cam = vis.available     #determine if the camaera is available
        idle = min(kb.seconds_since_last_key, f.mouse.seconds_since_last_event) 
        #choose the smaller time that the user hasn't used of keyboard or mouse
        self.elapsed_s += dt   #add 5 seconds


        # 1. timers
        self.work_s = 0.0 if idle >= C.BREAK_S else self.work_s + dt
        #if break > 5 minutes, rested, otherwise keep working(add 5 minutes)

        looked_away = (cam and vis.gaze_away_s >= C.LOOKAWAY_S) or idle >= C.LOOKAWAY_S
        # if idle>20s or camera see you look away with visual>20s, reset.
        self.screen_s = 0.0 if looked_away else self.screen_s + dt
        #look away then reset screen, otherwise increase 5 seconds
        work_min, screen_min = self.work_s / 60, self.screen_s / 60
        #translate to minutes

        # 2. remember the user's normal values once, at minute 10
        if self.normal is None and self.elapsed_s >= C.BASELINE * 60:
        #if haven't record own value and ran for 10 minutes already
            self.normal = (vis.blink_rate_per_min, kb.iki_mean_ms, kb.backspace_ratio)
            #store the user's own attributes

        # 3. loads (0-1) per body part
        wrist = (C.WRIST_TYPING_WEIGHT * ramp(kb.typing_burst_s / 60, C.WRIST_TYPING_S, C.WRIST_TYPING_FULL)
                 + C.WRIST_WORK_WEIGHT * ramp(work_min, C.WRIST_WORK_S, C.WRIST_WORK_FULL))
        eye = ramp(screen_min, C.EYE_LOOKAWAY_S, C.EYE_LOOKAWAY_FULL)
        neck = ramp(work_min, C.NECK_SITTING_S, C.NECK_SITTING_FULL)
        mind = 0.0


        if cam:  # consider head angle when there's camera
            neck = 0.7 * ramp(vis.head_pitch_deg, 0, 45) + 0.3 * neck
            # 0.7 angle adding 0.3 sitting
        if self.normal: #if recorded normal
            blink0, iki0, bs0 = self.normal
            if cam and blink0:
                drop = (blink0 - vis.blink_rate_per_min) / blink0   #calculate decreasement
                eye = 0.6 * ramp(drop, C.EYE_BLINK_DROP_S, C.EYE_BLINK_DROP_FULL) + 0.4 * eye   #update eye
            if iki0 and bs0 and kb.iki_mean_ms > 0: #if nomally not 0 and typing right now
                slower = (kb.iki_mean_ms - iki0) / iki0
                more_bs = (kb.backspace_ratio - bs0) / bs0
                mind = 0.5 * ramp(slower, C.MIND_SLOW_S, C.MIND_SLOW_FULL) \
                     + 0.5 * ramp(more_bs, C.MIND_BACKSPACE_S, C.MIND_BACKSPACE_FULL)
        loads = {"upper_extremity": wrist, "ocular": eye, "postural": neck, "cognitive": mind}

        # 4. scores move slowly toward load x 100 (up ~10 min, down ~3 min)
        for name, load in loads.items():
            old, target = self.parts[name], load * 100
            minutes = C.RISE_MINUTES if target > old else C.FALL_MINUTES
            self.parts[name] = old + (target - old) * dt / (minutes * 60)
            #increase slowly, decrease faster

        # 5. total = 0.6 x average + 0.4 x worst
        values = list(self.parts.values())  #take all the value
        total = round(C.AVERAGE_WEIGHT * sum(values) / 4 + C.MAX_WEIGHT * max(values), 1)
        level = ("low" if total < C.LEVEL_MODERATE else "moderate" if total < C.LEVEL_HIGH
                 else "high" if total < C.LEVEL_CRITICAL else "critical")   #display output

        # 6. alert: score high + user paused + not alerted in last 20 min
        alert = None    #default no alert
        #high enough and just idle
        if total >= C.ALERT_ON and idle >= C.ALERT_IDLE_S \
                and self.elapsed_s - self.last_alert_s >= C.ALERT_COOLDOWN_S:   #enough time just passed
            worst = max(self.parts, key=self.parts.get) #find the worst score
            alert = {"target": worst, "message": C.ADVICE[worst]}
            self.last_alert_s = self.elapsed_s  #record the current alert time

        return {"systemic_fatigue_score": total, "level": level,
                "components": {k: round(v, 1) for k, v in self.parts.items()},
                "calibrating": self.normal is None, "alert": alert}
