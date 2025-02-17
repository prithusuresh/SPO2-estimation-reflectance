import os
import pandas as pd
import numpy as np
from tqdm import tqdm
import pickle as pkl
from sklearn.linear_model import LinearRegression
import scipy.signal
from dtaidistance import dtw
import scipy.stats

import os
import numpy as np 
import pandas as pd
import pickle as pkl
import scipy
import scipy.signal

import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


def detrend(signal):
    R, IR = signal[:,0],signal[:,1]
    R_detrended = fit_trendline(R)[0]
    IR_detrended = fit_trendline(IR)[0]

    signal = np.concatenate([R_detrended,IR_detrended], axis = 1)

    return signal



def fit_trendline(y, fs = 600): 
    '''Fit Trendline for detrending '''
    model = LinearRegression()
    X = np.array([j for j in range(len(y))])

    X= X.reshape((-1,1))
    x = np.concatenate([X,X**2], axis = 1)
    model.fit(x,y)
    pred = model.predict(x)

    t = X.reshape(len(X))/fs
    return [np.array([y[j] - pred[j] + np.mean(y) for j in range(X.shape[0])]).reshape((-1,1)), pred, t]

def smooth(signal,window_len=50):
    #''' Smoothen and detrend signal by removing 50 Hz using notch and Savitzky-Golay Filter for smoothening''' 
  # num,denom = scipy.signal.iirnotch(50,1,600) ### How is the quality factor choosen?
  # notched = scipy.signal.lfilter(num,denom,signal)
  # y = savgol_filter(notched, window_len, 1) ### How is the window length and the polynomial required choosen?
  # detrend, pred, t = fit_trendline(y)
    y = pd.DataFrame(signal).rolling(window_len,center = True, min_periods = 1).mean().values.reshape((-1,))
    return y



def peaks_and_valleys(signal, prominence = 300, is_smooth = True , distance = 250):

    """ Return prominent peaks and valleys based on scipy's find_peaks function """

    if is_smooth:

        smoothened = smooth(signal)
        peak_loc = scipy.signal.find_peaks(smoothened, prominence = prominence, distance = distance)[0] #,scipy.signal.find_peaks(smoothened, prominence = prominence, distance = distance )[1]["prominences"]
    
        signal = signal*(-1)
        smoothened = smooth(signal)
        valley_loc = scipy.signal.find_peaks(smoothened, prominence = prominence,distance = distance)[0]
    
        final_peaks_loc, final_valley_loc = discard_outliers(smooth(signal),peak_loc,valley_loc)
    else:
        peak_loc = scipy.signal.find_peaks(signal, prominence = prominence,distance = distance)[0]
        signal = signal*(-1)
        valley_loc = scipy.signal.find_peaks(signal, prominence = prominence,distance = distance)[0]
    
        final_peaks_loc, final_valley_loc = discard_outliers(signal,peak_loc,valley_loc)
 
    return final_peaks_loc, final_valley_loc

def discard_outliers(signal,peaks,valleys):
    """Find peaks or valleys in a signal. 
    Returns peak, and groups of valleys"""
    val = [[valleys[x-1],valleys[x]] for x in range(1,len(valleys))]
    peak = {}
    for i in range(len(val)) :
        x= val[i]
        try:     
            peak[i] = int(peaks[np.where(np.logical_and(peaks> x[0],peaks < x[1]))[0][0]])
        except:
            pass
    i=0
    val_ = []
    while i<len(val):
        if i not in peak.keys():
            pass
        else:
            val_.append(val[i])
        i+=1
        
    try:
        assert len(peak) == len(val_)
    except AssertionError:
#         print ("peak: ", peak)
#         print ("valley: ",val)
#         print ("valley_: ",val_) 
#         import pdb;pdb.set_trace()

        return None,None
    
    
    final_val =list(set([x for j in val_ for x in j]))
    final_val.sort()
    final_peak = [peak[i] for i in peak.keys()]
    final_peak.sort()
 
    return final_peak,final_val

def return_info(signal,wlen, is_smooth):
    """ Get smoothened signal, peak location and valley location 
  Input: 
    signal: RAW SIGNAL"""

    detrended_signal = detrend(signal)
    R_signal = detrended_signal[:,0].reshape((-1,))
    IR_signal = detrended_signal[:,1].reshape((-1,))
    peaks_R, valleys_R = peaks_and_valleys(R_signal, is_smooth)
    peaks_IR, valleys_IR = peaks_and_valleys(IR_signal, is_smooth)
  
    if peaks_R is None or valleys_R is None or peaks_IR is None or valleys_IR is None:
<<<<<<< HEAD
#         print (" No valleys detected by scipy")
=======
>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
        return [None, None, None], [None, None,None]
    if is_smooth:
        return [smooth(signal[:,0]),peaks_R,valleys_R],[smooth(signal[:,1]),peaks_IR,valleys_IR]
    else:
        return [signal[:,0], peaks_R,valleys_R],[signal[:,1],peaks_IR,valleys_IR]

def plot_signal(signal,wlen, is_smooth = True):

    """ plot Red and IR signals along with peaks and valleys"""

    [R_signal,peaks_R, valleys_R],[IR_signal,peaks_IR, valleys_IR] = return_info(signal,wlen, is_smooth)

    if R_signal is not None and IR_signal is not None:
        plt.subplot(121)
        plt.title("SMOOTHENED")
        plt.scatter(valleys_R[0],R_signal[valleys_R[0]],c = "b")
        plt.plot(R_signal)
        plt.subplot(122)
        plt.plot(IR_signal)
        plt.show()

        plt.subplot(121)
        plt.title("LOCATIONS")
        plt.plot(R_signal)
        plt.scatter(peaks_R ,R_signal[peaks_R], c= "r")
        plt.scatter(valleys_R,R_signal[valleys_R], c= "g")
        plt.subplot(122)
        plt.plot(IR_signal)
        plt.scatter(peaks_IR, IR_signal[peaks_IR], c= "r")
        plt.scatter(valleys_IR , IR_signal[valleys_IR], c= "g")
        plt.show()

def assess_quality(R,IR):
    """ get cross-correlation coefficient"""
    R_signal= R[0]
    IR_signal = IR[0]

    return np.corrcoef(R_signal,IR_signal)[0][1]

def extract_cycles(data, show = True,harshness = 0.5):

    """extract location of only good cycles """

    signal,peaks,valleys = data[0],data[1],data[2]
    
    peaks.sort()
  
    val = [[valleys[x-1],valleys[x]] for x in range(1,len(valleys))]
    peak = []
    i=0
    while i<len(val):
        try: 
            peak.append(peaks[int(np.where(np.logical_and(peaks > val[i][0],peaks < val[i][1]))[0][0])])
            i+=1
        except:
            val.pop(i)

    val = np.array(val,ndmin = 2)
    mean = np.mean(np.diff(val,axis=1))
    std = np.std(np.diff(val,axis=1))

    while harshness <=1:
        good_valleys = [x for x in val if np.diff(x) > mean-harshness*std and np.diff(x) < mean+harshness*std]
        if len(good_valleys)<3:
            harshness +=0.1
        else:
            break    
    try: 
        assert good_valleys is not None
    except AssertionError:
#         print ("No good valleys")
        return None,None
    
    good_peaks = []
    for i in good_valleys: 
        good_peaks.append(peak[int(np.where(np.logical_and(peak > i[0], peak < i[1]))[0][0])])
    
    good_peaks.sort()
    good_valleys = np.asarray(good_valleys)
    return good_peaks, good_valleys


def valley_matching(R_valleys, IR_valleys):
    R_valleys = np.array(R_valleys, ndmin = 2)
    IR_valleys = np.array(IR_valleys, ndmin = 2)

    minimum = min(R_valleys.shape[0], IR_valleys.shape[0])
<<<<<<< HEAD

=======
#   /rint (minimum)
>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
    dist = []
    for r in R_valleys:
        for i in IR_valleys: 
            if np.sum(abs(i-r)) <= 10:
                loc = i
<<<<<<< HEAD

                if not any(loc is x for x in dist):
                    dist.append(loc)
                    
    valleys = dist

=======

                if not any(loc is x for x in dist):
                    dist.append(loc)
                    
    valleys = dist
#   print (valleys)
  # /[dist[x][0] for x in np.sort(np.array(list(dist.keys())))[:minimum]]

>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
    return valleys


def peak_matching(R_peaks, IR_peaks):
    R_peaks = np.array(R_peaks)
    IR_peaks = np.array(IR_peaks)
  
    minimum = min(R_peaks.shape[0], IR_peaks.shape[0])
<<<<<<< HEAD

=======
#   print (minimum)
>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
    dist = []
    for r in R_peaks:
        for i in IR_peaks: 
            if np.sum(abs(i-r)) <= 10:
                loc = i
                if loc not in dist:
                    dist.append(loc)
<<<<<<< HEAD
=======
#     peaks = dist[0][:minimum]
    
  # [dist[x][0] for x in np.sort(np.array(list(dist.keys())))[:minimum]]
>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
    dist.sort()
    peaks = dist
    return peaks




def calculate_R_from_cycle(signal, wlen, show = False, tx_mode = True):

    """ Calculate Final R value """

    R,IR = return_info(signal,wlen, True)

    if R[1] is None or R[2] is None or IR[1] is None or IR[2] is None:
<<<<<<< HEAD
#         print ("Not Returning R_value. Poor Signal")
=======
        print ("Not Returning R_value. Poor Signal")
>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
        return None
    peaks_R,valley_groups_R = extract_cycles(R)
    peaks_IR,valley_groups_IR = extract_cycles(IR)

    if peaks_R is None or valley_groups_R is None or peaks_IR is None or valley_groups_IR is None or R[0] is None or IR[0] is None:
    
#         print ("Not Returning R_value. Poor peaks and valleys")
        return None
    else:
<<<<<<< HEAD
        check = 0.9 if tx_mode == True else 0.80
=======
>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
 
        
        corr = assess_quality(R,IR)
 
        if corr > check:
        
            pass
#             print (corr)
#             print ("Good")

        else:
#             print ("POOR correlation")
#             print (corr)
            return None
        
        if tx_mode:
            peaks_R,valley_groups_R = extract_cycles(R)
            peaks_IR,valley_groups_IR = extract_cycles(IR)
            
        

            try:
                val = np.array(valley_matching(valley_groups_R, valley_groups_IR))
                peaks = list(set(peak_matching(peaks_R,peaks_IR)))
                peaks.sort()
            except Exception as e:
#                 print (e)
#                 print ("wutt?")
                return None
                import pdb;pdb.set_trace()
                
            peak={}
            for i in range(len(val)) :
                x= val[i]
                try:     
                    peak[i] = int(peaks[np.where(np.logical_and(peaks> x[0],peaks < x[1]))[0][0]])
                except:
                    pass

            i=0
            val_ = []
        
            while i<len(val):
                if i not in peak.keys():
                    pass
                else:
                    val_.append(val[i])
                i+=1
            try:
                assert len(peak) == len(val_)
            except AssertionError:

#                 print ("peak: ", peak)
#                 print ("valley: ",val)
#                 print ("valley_: ",val_) 
                import pdb;pdb.set_trace()


            final_valleys = val_
            final_peaks = [peak[i] for i in peak.keys()]
            final_peaks.sort()

<<<<<<< HEAD
        elif tx_mode is False:
            peaks_R,valley_groups_R = extract_cycles(R)
            peaks_IR,valley_groups_IR = extract_cycles(IR)
            
#             print ("Reflectance Mode: ")
#             print (valley_groups_R, valley_groups_IR)

            try:
                final_valleys = np.concatenate([valley_groups_R,valley_groups_IR])
#             print ("final_valleys: ", final_valleys)
                final_peaks = np.union1d(peaks_R,peaks_IR)
            
                final_peaks.sort()
            except:
                return None
=======
        final_valleys = np.array(valley_matching(valley_groups_R, valley_groups_IR))
        final_peaks = list(set(peak_matching(peaks_R,peaks_IR)))
        final_peaks.sort()

>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
        if show:
            unravel_val = list(set(np.asarray(final_valleys).ravel()))
            unravel_val.sort()
            plt.subplot(121)
            plt.title("Final cycles")
            plt.plot(R[0])
            plt.scatter(final_peaks, R[0][final_peaks], c= "r")
            plt.scatter(final_valleys, R[0][final_valleys], c= "g")
            plt.subplot(122)
            plt.title("Final cycles")
            plt.plot(IR[0])
            plt.scatter(final_peaks, IR[0][final_peaks], c= "r")
            plt.scatter(final_valleys, IR[0][final_valleys], c= "g")
            plt.show()

        R_ratio = ac_dc(R[0], final_peaks, final_valleys)
        calculate_R_from_cycle.R_components = [ac_dc.ac, ac_dc.dc]
<<<<<<< HEAD
#         print ("R_AC AND R_DC :", calculate_R_from_cycle.R_components)

        IR_ratio = ac_dc(IR[0], final_peaks, final_valleys)
        calculate_R_from_cycle.IR_components = [ac_dc.ac, ac_dc.dc]
#         print ("IR_AC AND IR_DC : ", calculate_R_from_cycle.IR_components)

        if tx_mode:
            if R_ratio is None or IR_ratio is None:
#                 print ("R_ratio or IR_ratio is NONE")
                return None
            else:
                R_value = R_ratio/IR_ratio
                
        else:
            if R_ratio is None or IR_ratio is None:
#                 print ("R_ratio or IR_ratio is NONE")
                return None
            else:
                R_value = np.mean(R_ratio)/np.mean(IR_ratio)
#             R_value = np.mean(R_ratio)/np.mean(IR_ratio)
        return R_value
=======
        print ("R_AC AND R_DC :", calculate_R_from_cycle.R_components)
        
        IR_ratio = ac_dc(IR[0], final_peaks, final_valleys)
        calculate_R_from_cycle.IR_components = [ac_dc.ac, ac_dc.dc]
        print ("IR_AC AND IR_DC : ", calculate_R_from_cycle.IR_components)
        
        
        if R_ratio is None or IR_ratio is None:
            return None
        else:
            R_value = R_ratio/IR_ratio
            return R_value
>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b

def ac_dc(signal,peaks, val):

    """ Get ac and dc component of each signal"""
    ac_dc.dc = []

    ac_dc.ac = []
    
    peaks.sort()

    val = list(val)
    i=0
    while i <len(val):
        try:
<<<<<<< HEAD
            index = int(np.where(np.logical_and(peaks > val[i][0], peaks < val[i][1]))[0][0])
            i+=1
        
        except:
            import pdb;pdb.set_trace()
            val.pop(i)

    peaks = list(peaks)
    peaks.sort()
=======

            index = int(np.where(np.logical_and(peaks > val[i][0], peaks < val[i][1]))[0])
            i+=1
        except TypeError:
            val.pop(i)

            
>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
    for i in range(len(val)):
        try:
            assert signal[peaks[i]] > (signal[val[i][0]]+signal[val[i][1]])/2 #and peaks[i]>val[i][0] and peaks[i]<val[i][1]
            
        except AssertionError:
            peaks.pop(i)       
            val.pop(i)
<<<<<<< HEAD
=======
           
            i -= 1
>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
            continue
        except IndexError:
            break
  
        ac_dc.dc.append((signal[val[i][0]]+signal[val[i][1]])/2)
        ac_dc.ac.append(signal[peaks[i]] - (signal[val[i][0]]+signal[val[i][1]])/2)
 
    
    if len(ac_dc.ac) == 0 or len(ac_dc.dc) == 0:
#         print ("No ac or Dc components")
        return None
    
    try:
<<<<<<< HEAD
#         print ("RATIO: ")
        ratio = np.array(ac_dc.ac)/np.array(ac_dc.dc)
#         print (ratio)
=======
        print ("RATIO: ")
        ratio = np.array(ac_dc.ac)/np.array(ac_dc.dc)
        print (ratio)
>>>>>>> b76f2f3746db9558c81da0a281a974c0bda2794b
    except Exception as e:
        print (e)
    
    
    return ratio


def calibrate_and_get_model(show = False):
    
    with open("Calibration_curve.txt", "r") as f:
        points = f.readlines()

    spo2 = np.array([int(x.split("\t")[0]) for x in points])
    R_truth = np.array([float(x.split("\t")[1].rstrip("\n")) for x in points]).reshape((-1,1))
    SPO2_model = LinearRegression()
    SPO2_model.fit(np.concatenate([R_truth, R_truth**2],axis = 1), spo2)

    if show: 
        pred = SPO2_model.predict(np.concatenate([R_truth, R_truth**2],axis = 1))
        plt.plot(R_truth, pred)
        plt.show()

    return SPO2_model

def get_spo2(R_values, SPO2_model):
    R_values = np.asarray(R_values).reshape((-1,1))
    pred = SPO2_model.predict(np.concatenate([R_values,R_values**2], axis = 1))  
#     print ("SPO2: ", np.mean(pred))
    return pred


# Feature Extraction

def mean(signal):
    mean_R = np.mean(signal[:,0])
    mean_IR = np.mean(signal[:,1])
    
    return [mean_R,mean_IR]

def variance(signal):
    var_R = np.var(signal[:,0])
    var_IR = np.var(signal[:,1])
    
    return [var_R,var_IR]

def correlation(signal):
    R = signal[:,0]
    IR = signal[:,1]

    return [np.corrcoef(signal[:,0],signal[:,1])[0][1]]




def manhattan_dist(R, IR):
    R = np.array(R)
    IR = np.array(IR)
    
    minimum = min(R.shape[0], IR.shape[0])

    dist = []
    for r in R:
        for i in IR: 
            if np.sum(abs(i-r)) <= 10:
                loc = i
                if loc not in dist:
                    dist.append(np.sum(abs(i-r)))
    dist.sort()
    return sum(dist)
    
def manhattan(signal):
    R = signal[:,0]
    IR = signal[:,1]
    R_peaks,R_valleys = peaks_and_valleys(R, is_smooth = False)
    IR_peaks,IR_valleys = peaks_and_valleys(IR, is_smooth = False)
    
    peak_dist = manhattan_dist(R_peaks, IR_peaks)
    valley_dist = manhattan_dist(R_valleys, IR_valleys)
    
    return [peak_dist,valley_dist]
    

def dtw_measure(signal):
    R = np.asarray(signal[:,0], dtype = np.double)
    IR = np.asarray(signal[:,1], dtype = np.double)
    
    return [dtw.distance_fast(R,IR)]

def skew_(signal):
    R = np.asarray(signal[:,0])
    IR = np.asarray(signal[:,1])
    
    import scipy.stats
    
    R_skew = scipy.stats.skew(R)
    IR_skew = scipy.stats.skew(IR)
    
    return [R_skew,IR_skew]

def kurt(signal):
    R = np.asarray(signal[:,0])
    IR = np.asarray(signal[:,1])
    
    from scipy.stats import kurtosis
    R_kurt = kurtosis(R)
    IR_kurt = kurtosis(IR)
       
    return [R_kurt, IR_kurt]

def mean_values(signal):
    R = np.asarray(signal[:,0])
    IR = np.asarray(signal[:,1])
    
    R_peaks,R_valleys = peaks_and_valleys(R, is_smooth = False)
    IR_peaks,IR_valleys = peaks_and_valleys(IR, is_smooth = False)
    
    R_mean_peaks = np.average(R[R_peaks])
    R_mean_valleys = np.average(R[R_valleys])
    
    IR_mean_peaks = np.average(IR[IR_peaks])
    IR_mean_valleys = np.average(IR[IR_valleys])
    
    return [R_mean_peaks,R_mean_valleys,  IR_mean_peaks, IR_mean_valleys]
    
def euclidian_dist(signal):
    R = np.asarray(signal[:,0])
    IR = np.asarray(signal[:,1])
    
    dist = np.sqrt(np.sum((R-IR)**2))
    return [dist]

def trendline_coeffecients(signal):
    R = np.asarray(signal[:,0])
    IR = np.asarray(signal[:,1])
    
    R_model = LinearRegression()
    IR_model = LinearRegression()
    
    X = np.array([j for j in range(len(R))])

    X= X.reshape((-1,1))
    x = np.concatenate([X,X**2], axis = 1)
    R_model.fit(x,R)
    IR_model.fit(x,IR)
    
    R_coeff = R_model.coef_
    IR_coeff = IR_model.coef_
    
    R_coeff = np.append(R_coeff,R_model.intercept_)
    IR_coeff = np.append(IR_coeff,IR_model.intercept_)
    
    coefficients = np.concatenate([R_coeff,IR_coeff])
    return coefficients
    
    

def extract_features(signal, is_smooth = True):
    
    if is_smooth:
        signal = np.concatenate([smooth(signal[:,0]).reshape((-1,1)),smooth(signal[:,1]).reshape((-1,1))], axis = 1).reshape((-1,2))
    
    
    functions = [mean,variance,correlation, manhattan, dtw_measure,kurt,skew_, mean_values, euclidian_dist, trendline_coeffecients]
    
    features=np.array([])
    for function in functions:
        f = np.asarray(function(signal))
        features = np.concatenate([features,f])
            
    return features

def calibrate(args):
    
    
    train_df = pd.read_csv("saved_data/model.csv")
    train_df.columns = [i for i in range(len(train_df.columns))]

    feature_data = pd.read_csv("saved_data/features.csv")
    feature_data.columns = [i for i in range(len(feature_data.columns))]

    p_column= len(feature_data.columns)-1
    spo2_column = p_column - 1
    r_column = spo2_column -1
    ref_r_column = r_column - 1
    calibrated= []
    
    default_test = args

    test_df= feature_data[feature_data[p_column].isin(default_test)].iloc[:,[ref_r_column,spo2_column,p_column]]




    for p in test_df[p_column].unique():
        if p in default_test:       

            for run in range(4,0,-1):
                lower = run*5 + 70
                upper = lower + 5
                try:
                    calibration_df = test_df[(test_df[p_column] == p) & (test_df[spo2_column] > lower) & (test_df[spo2_column] < upper)].sample(5)
                    break
                except ValueError:
                    continue

            line = []    
            predictions = []


            for i in calibration_df.index:
                spo2 = calibration_df.loc[i,spo2_column]
                R = calibration_df.loc[i,ref_r_column]
                m = train_df[1]
                c = train_df[2]
                x =np.asarray((spo2 - c)/m)
                minimum = np.argmin(np.abs(x-R))
                line.append(minimum)
                predictions.append(train_df.iloc[minimum,1]*R + train_df.iloc[minimum,2])

            x = np.linspace(0.2,1.5)
            mode = scipy.stats.mode(line)[0][0]

            y = train_df.iloc[mode,1]*x + train_df.iloc[mode,2]
            calibrated.append(train_df.iloc[mode,0])
            
            
    return calibrated, train_df, (x,y)
