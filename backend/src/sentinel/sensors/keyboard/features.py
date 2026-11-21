
import statistics

def keys_per_min(timestamps: list[float],now:float)->float:
    count=0
    for i in timestamps:
        if now-60 <= i <= now:# only count timestamps within the last 60 seconds
            count+=1
    return float(count)


def inter_key_intervals(timestamps: list[float])->list[float]:
    result=[]
    if len(timestamps)<2:#edge case,no intervals can be calculated
        return []
    for i in range(1,len(timestamps)):
        interval=timestamps[i]-timestamps[i-1]
        if interval<2:
            result.append(interval)
    return result
    

def iki_mean_ms(intervals: list[float])->float:
    if len(intervals)==0:# Handle empty list
        return 0.0
    return sum(intervals)/len(intervals)*1000

def iki_cv(intervals: list[float])->float:
    if len(intervals)<2:# Handle empty list or single interval
        return 0.0
    mean=statistics.mean(intervals)
    if mean==0:# Handle mean=0 to avoid division by zero
        return 0.0
    stdev=statistics.pstdev(intervals)#population standard deviation
    return stdev/mean

def typing_burst_s(timestamps: list[float], now: float)->float:
    if not timestamps:
        return 0.0
    if now-timestamps[-1]>2:#last key was more than 2 seconds ago
        return 0.0
    last_burst_start=timestamps[-1]#backward loop
    for i in range(len(timestamps)-1,0,-1):#range(start, stop, step)
        if timestamps[i]-timestamps[i-1]>2:
            break
        else:
            last_burst_start=timestamps[i-1]
    return now-last_burst_start
    

def backspace_ratio(backspaces: int, total_keys: int)->float:
    if total_keys == 0:
        return 0.0
    return float(backspaces) / float(total_keys)

def seconds_since_last_key(timestamps: list[float], now: float, start_time: float)->float:
    if not timestamps:
        return now - start_time
    return now - timestamps[-1]