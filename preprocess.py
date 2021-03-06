import sys
import os
import pandas as pd
import numpy as np
from numpy import linalg as LA


def main():
    # Load in Worm Motion Data
    simulation = 'trial_1_halfres'
    motion_df = pd.read_csv('/clusterhome/chaudhry/openworm/simulations/{}/worm_motion_log.txt'.format(simulation), delim_whitespace=True, header=None)

    # Reorganize Dataframe
    motion_df.rename(columns={motion_df.columns[0] : 'Time_Step', motion_df.columns[1] : 'X', motion_df.columns[101] : 'Y', motion_df.columns[201] : 'Z'}, inplace=True)
    for pos in range(99):
        motion_df.rename(columns={motion_df.columns[pos+2] : 'X_' + str(pos)}, inplace=True)
        motion_df.rename(columns={motion_df.columns[pos+102] : 'Y_' + str(pos)}, inplace=True)
        motion_df.rename(columns={motion_df.columns[pos+202] : 'Z_' + str(pos)}, inplace=True)

    # Drop Z Coordinates
    motion_df.drop(motion_df.columns[201:301], axis=1, inplace=True)

    # Drop First 1000 data points since these only represent the worm's initialization
    motion_df.drop(motion_df.index[0:999], inplace=True)
    
    Time = len(motion_df) - 1
    Positions = 95

    print 'Time = ' + str(Time)

    # Create Array with Normalized Relative Vectors for every other point along the midline.
    L = np.zeros((Time,Positions,2))
    R = np.zeros((Time,Positions,2))
    motion = motion_df.values

    for t in range(Time):
        for pos in range(Positions):
            L[t,pos,0] = (motion[t,  2+(pos)]   - motion[t,  2+(pos+2)]) / LA.norm([motion[t,2+(pos)]   - motion[t,2+(pos+2)], motion[t,102+(pos)]   - motion[t,102+(pos+2)]])
            L[t,pos,1] = (motion[t,102+(pos)]   - motion[t,102+(pos+2)]) / LA.norm([motion[t,2+(pos)]   - motion[t,2+(pos+2)], motion[t,102+(pos)]   - motion[t,102+(pos+2)]])
            R[t,pos,0] = (motion[t,  2+(pos+4)] - motion[t,  2+(pos+2)]) / LA.norm([motion[t,2+(pos+4)] - motion[t,2+(pos+2)], motion[t,102+(pos+4)] - motion[t,102+(pos+2)]])
            R[t,pos,1] = (motion[t,102+(pos+4)] - motion[t,102+(pos+2)]) / LA.norm([motion[t,2+(pos+4)] - motion[t,2+(pos+2)], motion[t,102+(pos+4)] - motion[t,102+(pos+2)]])


    # Inverse Kinematics to Derive Angles Between Positions
    angles = np.zeros((Time,Positions))
    c_Ang = np.zeros((Time,Positions))
    s_Ang = np.zeros((Time,Positions))

    for t in range(Time):
        for pos in range(Positions):
            c_Ang = abs(L[t,pos,0:2].dot(R[t,pos,0:2]))
            s_Ang = np.cross(L[t,pos,0:2],R[t,pos,0:2])
            if s_Ang > 0:
                angles[t,pos] =   (1 - c_Ang)
            else:
                angles[t,pos] = - (1 - c_Ang)

    # Scale up the Angles so the network is more sensitive to perturbations
    angles    = 10 * angles

    print 'Angles Shape = ' + str(angles.shape)

    # Create More Training Data by Adding Gaussian Noise
    mu, sigma = 0, 0.025
    noise1 = np.random.normal(mu, sigma, [Time,Positions])
    noise2 = np.random.normal(mu, sigma, [Time,Positions])
    noise3 = np.random.normal(mu, sigma, [Time,Positions])
    noise4 = np.random.normal(mu, sigma, [Time,Positions])
    angles_noise1 = angles + noise1
    angles_noise2 = angles + noise2
    angles_noise3 = angles + noise3
    angles_noise4 = angles + noise4

    # Import and Label Muscle Data
    muscles_df = pd.read_table("/clusterhome/chaudhry/openworm/simulations/{}/muscles_activity_buffer.txt".format(simulation), delim_whitespace=True, header=None)

    # Drop First 1000 data points since these only represent the worm's initialization
    muscles_df.drop(muscles_df.index[0:1000], inplace=True)
    muscles = muscles_df.values

    #muscles_df = pd.concat([motion_df['Time_Step'],muscles_df], axis=1)

    # Create Training and Test Sets.
    # Still need to sample randomly.

    angles_train        = np.zeros((Time/2,Positions))
    angles_noise1_train = np.zeros((Time/2,Positions))
    angles_noise2_train = np.zeros((Time/2,Positions))
    angles_noise3_train = np.zeros((Time/2,Positions))
    angles_noise4_train = np.zeros((Time/2,Positions))
    angles_test         = np.zeros((Time/2,Positions))
    muscles_train       = np.zeros((Time/2,96))
    muscles_test        = np.zeros((Time/2,96))

    for i in range(225):
        angles_noise1_train[20 * (i) : 20 * (i+1),:]  = angles_noise1[20  * (2*i)  : 20 * (2*i+1), : ]
        angles_noise2_train[20 * (i) : 20 * (i+1),:]  = angles_noise2[20  * (2*i)  : 20 * (2*i+1), : ]
        angles_noise3_train[20 * (i) : 20 * (i+1),:]  = angles_noise3[20  * (2*i)  : 20 * (2*i+1), : ]
        angles_noise4_train[20 * (i) : 20 * (i+1),:]  = angles_noise4[20  * (2*i)  : 20 * (2*i+1), : ]
        angles_train[20 * (i) : 20 * (i+1), : ]       = angles[20  * (2*i)  : 20 * (2*i+1), : ]
        angles_test[20 * (i) : 20 * (i+1),  : ]       = angles[20  * (2*i+1): 20 * (2*i+2), : ]
        muscles_train[20 * (i) : 20 * (i+1),: ]       = muscles[20 * (2*i)  : 20 * (2*i+1), : ]
        muscles_test[20 * (i) : 20 * (i+1), : ]       = muscles[20 * (2*i+1): 20 * (2*i+2), : ]

    print 'Angles_Train 0,1 = ' + str([angles_train[0][0],angles_train[1][0]])
    print 'Muscles_train 0,1 = ' + str([muscles_train[0][0],muscles_train[1][0]])
    print 'Angles_Train 30,31 = ' + str([angles_train[30][0],angles_train[31][0]])
    print 'Muscles_train 30,31 = ' + str([muscles_train[30][0],muscles_train[31][0]])

    angles_train_large  = np.vstack((angles_train,angles_noise1_train,angles_noise2_train,angles_noise3_train,angles_noise4_train))
    muscles_train_large = np.vstack((muscles_train,muscles_train,muscles_train,muscles_train,muscles_train))

    directory = '/clusterhome/chaudhry/experiments/data/' + simulation + '_' + 'shifted_1' 
    if not os.path.exists(directory):
        os.makedirs(directory)

    np.save(directory + '/angles_train', angles_train_large)
    np.save(directory + '/angles_test', angles_test)
    np.save(directory + '/muscles_train', muscles_train_large)
    np.save(directory + '/muscles_test', muscles_test)


if __name__ == "__main__":
    main()