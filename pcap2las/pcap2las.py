import argparse
import os
from contextlib import closing

import numpy as np
import laspy

from ouster import client, pcap


def extract_pcap(pcap_path: str,
                 metadata_path: str,
                 chunk_size: int) -> np.array:
    with open(metadata_path, 'r') as f:
        metadata = client.SensorInfo(f.read())
    source = pcap.Pcap(pcap_path, metadata)

    with closing(source):
        # precompute xyzlut to save computation in a loop
        xyzlut = client.XYZLut(metadata)

        # pre-allocate a numpy array
        factor = 2**16
        frames = np.zeros((0, 8), dtype=np.int64)

        # create an iterator of LidarScans from pcap
        scans = iter(client.Scans(source))

        for idx, scan in enumerate(scans):

            if (idx % chunk_size == 0):
                frames = np.vstack((frames, np.zeros((factor*chunk_size, 8), dtype=np.int64)))

            # copy per-column timestamps for each channel
            col_timestamps = scan.header(client.ColHeader.TIMESTAMP)
            timestamps = np.tile(col_timestamps, (scan.h, 1))

            # grab channel data
            fields_values = [scan.field(ch) for ch in client.ChanField]

            # use integer mm to avoid loss of precision casting timestamps
            xyz = (xyzlut(scan) * 1000).astype(np.int64)

            # get all data as one H x W x 8 int64 array for savetxt()
            frame = np.dstack((timestamps, *fields_values, xyz))

            # not necessary, but output points in "image" vs. staggered order
            frame = client.destagger(metadata, frame)

            # save scan to pre-allocated array
            # frames = np.append(frames, frame.reshape(-1, frame.shape[2]))
            print(f"Extracting pcap lidar packet #{idx+1}", end="\r")
            frames[idx*factor:idx*factor+factor, :] = frame.reshape(-1, frame.shape[2])

    # remove all zero entries
    frames = frames[~np.all(frames == 0, axis=1)]

    return frames


def generate_azimuths(data: np.array) -> np.array:
    """Can be added if useful. Invert from X and Y coordinates"""
    return data


def save_las(pcap_path: str,
             format: str,
             data: np.array) -> None:
    print("\nPrepping lidar data for export...")

    # create las header
    header = laspy.LasHeader(point_format=1, version="1.4")
    header.add_extra_dims(
        [
            laspy.ExtraBytesParams(name="nanoseconds", type=np.uint64),
            laspy.ExtraBytesParams(name="range", type=np.double),
            laspy.ExtraBytesParams(name="signal", type=np.uint16),
            laspy.ExtraBytesParams(name="near_ir", type=np.uint16),
            laspy.ExtraBytesParams(name="reflectivity", type=np.uint16)
        ]
    )
    header.offsets = np.min(np.double(data[:, 5:] / 1000), axis=0)
    header.scales = np.array([0.01, 0.01, 0.01])

    # set up las
    las = laspy.LasData(header)
    las.nanoseconds = data[:, 0]
    las.range = np.double(data[:, 1] / 1000)
    las.signal = data[:, 2]
    las.near_ir = data[:, 3]
    las.reflectivity = data[:, 4]
    las.x = np.double(data[:, 5] / 1000)
    las.y = np.double(data[:, 6] / 1000)
    las.z = np.double(data[:, 7] / 1000)

    # write to las file
    root, _ = os.path.splitext(pcap_path)
    if (format == "las"):
        las_path = root + ".las"
    else:
        las_path = root + ".laz"
    print(f"Writing lidar data to {las_path}...")
    las.write(las_path)


def get_args():
    description = "Convert PCAP files to LAS format."

    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('pcap_path',
                        metavar='PCAP',
                        help='path to pcap file')
    parser.add_argument('metadata_path',
                        metavar='METADATA',
                        help='path to metadata json')
    parser.add_argument('--chunk-size',
                        type=int,
                        default=1000,
                        help='larger values are faster for large pcap files')
    parser.add_argument('--format',
                         type=str,
                         default='laz',
                         help='standard (las) or compressed (laz) format')

    args = parser.parse_args()

    if not args.pcap_path or not os.path.exists(args.pcap_path):
        print(f"PCAP file does not exist: {args.pcap_path}")
        exit(1)
    if not args.metadata_path or not os.path.exists(args.metadata_path):
        print(f"Metadata file does not exist: {args.metadata_path}")
        exit(1)

    if not args.format == "las" and not args.format == "laz":
        print(f"'{args.format}' is not a valid format. Only 'las' or 'laz' accepted.")
        exit(1)

    return args


def main():
    # get CLI input
    args = get_args()

    # extract pcap lidar records
    data = extract_pcap(args.pcap_path, args.metadata_path, args.chunk_size)

    # generate azimuths from xy coordinates (for downstream filtering)
    # data = generate_azimuths(data)

    # save to las(z) file
    save_las(args.pcap_path, args.format, data)


if __name__ == "__main__":
    main()