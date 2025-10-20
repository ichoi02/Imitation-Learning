# How to preprocess KIT dataset

## 1. Prepare raw dataset
Move .c3d and _mmm.xml files to /dataset/c3d and /dataset/xml

## 2. Run c3d2trc.py
Move to base directory

Run in terminal:
```
python dataset/c3d2trc.py [start_index] [end_index]
```
Files are saved in /dataset/trc/.

Name format: [index number]_[subject number].trc

## 3. Scale .osim models manually in OpenSim 
Use /dataset/models/H2190_kit.osim

Load /dataset/scale_settings/scale_set.xml

Load marker data (.trc) from /dataset/trc/ with target subject

Set measurements between times 0.0-0.1s

Check scale factors (around 0.9-1.1 is nominal) and static pose

Run scale tool

Right click model in Navigator and save as H2190_kit_{subject number:05d}.osim

Repeat for every subject

## 4. Run auto_IK.py
Run in terminal:
```
python dataset/auto_IK.py [start_index] [end_index]
```

## 5. Run auto_analysis.py
Run in terminal:
```
python dataset/auto_analysis.py [start_index] [end_index]
```

## 6. Done!
