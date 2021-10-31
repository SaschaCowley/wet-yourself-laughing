# Wet Yourself Laughing

Prototype implementation of a bodily play EMS game in which players control how much their opponent is tickled by a feather by smiling, and must not laugh lest their own water balloon burst. This game was developed as a part of the unit _FIT2082: Computer Science Research Project_ at Monash University.

## Structure

There are essentially two components to this software:

* The python code, which is really the brains of the game; and
* The Arduino controller code, which is used to switch the EMS signal.

## Running

The game should be run by executing `py wysl` at the root of this repo. Make sure all dependencies are installed first.

## Configuration

The game is fairly configurable. Configuration fields, types and defaults are shown below.

| Section     | Key               | Type  | Default | Description                                                                           |
|-------------|-------------------|-------|---------|---------------------------------------------------------------------------------------|
| expression  | camera_index      | int   | 0       | Index of the video input to use for expression recognition                            |
| expression  | mtcnn             | bool  | False   | Whether or not to use the MTCNN network to find faces. More accurate but slower       |
| expression  | happy_weight      | int   | 1       | Weight of the 'happy' expression when calculating the weighted average expression     |
| expression  | surprise_weight   | int   | 1       | Weight of the 'surprised' expression when calculating the weighted average expression |
| expression  | low_threshhold    | float | 0.2     | Threshold for a smile to be considered low intensity                                  |
| expression  | medium_threshhold | float | 0.3     | Threshold for a smile to be considered medium intensity                               |
| expression  | high_threshhold   | float | 0.4     | Threshold for a smile to be considered high intensity                                 |
| laughter    | microphone_index  | int   | 0       | Index of the audio input to use for laughter detection                                |
| laughter    | chunk_duration    | float | 0.05    | Length of an audio segment that will be taken for laughter detection                  |
| laughter    | threshhold        | float |         | Minimum volume required to record a hit                                               |
| laughter    | records           | int   | 10      | Number of recently recorded volumes to keep                                           |
| laughter    | hits              | int   | 5       | Number of hits required to trigger laughter detection                                 |
| arduino     | port              | str   |         | Identifier of the port to which the Arduino is connected (ex. "COM5"                  |
| arduino     | baudrate          | int   | 9600    | Baudrate of the serial connection to the Arduino                                      |
| network     | remote_ip         | str   |         | IP v4 address of the other player's machine                                           |
| network     | remote_port       | int   | 5005    | Port on the other player's machine to which to send UDP packets                       |
| network     | local_ip          | str   |         | Local IP v4 address of this machine. Can be detected by setup                         |
| network     | local_port        | int   | 5005    | Local port for receiving UDP packets from the other player's machine                  |
| game        | slower_tickle     | int   | 1000    | Rate at which to pulse EMS on the player's feather hand for a slower tickle           |
| game        | slow_tickle       | int   | 500     | Rate at which to pulse EMS on the player's feather hand for a slow tickle             |
| game        | fast_tickle       | int   | 250     | Rate at which to pulse EMS on the player's feather hand for a fast tickle             |
| game        | faster_tickle     | int   | 100     | Rate at which to pulse EMS on the player's feather hand for a faster tickle           |
| game        | feather_channel   | int   | 1       | Which relay the EMS for the player's feather hand is connected to                     |
| game        | balloon_channel   | int   | 2       | Which relay the EMS for the player's balloon hand is connected to                     |
| game        | squeeze_duration  | float | 5.0     | How long to squeeze the balloon for before assuming it has burst                      |


## The controler

The Arduino controller code enables the relays on the Arduino to be controlled and queried via serial to allow digital switching of EMS from other programs. It supports the following commands:

| Command                   | Syntax              | Return                  |
|---------------------------|---------------------|-------------------------|
| Switch relay on           | `+<relay>`            | [Nothing]             |
| Switch relay off          | `-<relay>`            | [Nothing]             |
| Periodically pulse relay  | `!<relay><interval>`  | [Nothing]             |
| Query relay state         | `?<relay>`            | `0` if off; `1` if on |

* `<relay>` must be one of 'A', 'B', 'C' or 'D' for relays 1-4, respectively. Currently, relay 1 maps to pin 35, 2 to 37, 3 to 39 and 4 to 41.
* `<interval>` must be an integer number of milliseconds to wait between switching the state of the given relay. The interval between successive switches should always be equal to or exceed this interval. Set to 0 to disable pulsing the relay. Note that the state of the relay after pulsing is stopped is not guaranteed.

For example, to turn relay 1 on, you would send `+A`. To turn it off, `-A`. To pulse it 10 times per second, `!A100`. And to check if it's on or off, `?A` (which would send back `0` or `1`).


## Known issues

* The configuration filename is currently hard-coded and configuration object is loaded outside of a method, class or `if __name__ == '__main__'`
* The waveform plotting is very inelegant.
* The keyboard loop should probably be the parent thread.
* Game exit is not graceful, as the keyboard thread is not terminated automatically.
* The two layers of input with the same prompt is confusing.
