import math
import os
import random
import json
import csv
import argparse
import logging
from configparser import ConfigParser


class Wolf:
    def __init__(self, x_pos, y_pos):
        self.x = x_pos
        self.y = y_pos


class Sheep:
    def __init__(self, x_pos, y_pos):
        self.x = x_pos
        self.y = y_pos


def sheep_move(sheep_list, sheep_move_dist):
    for obj in sheep_list:
        if obj:
            option = random.randrange(1, 4)
            if option == 1:
                obj.x -= sheep_move_dist
            elif option == 2:
                obj.x += sheep_move_dist
            elif option == 3:
                obj.y -= sheep_move_dist
            else:
                obj.y += sheep_move_dist

    log = "sheep_move({}, {}) was called".format(sheep_list, sheep_move_dist)
    logging.debug(log)


def nearest_sheep(sheep_list, wolf):
    dist = math.inf
    index = None
    for i, obj in enumerate(sheep_list):
        if obj:
            temp_dist = math.sqrt(pow((wolf.x - obj.x), 2) + pow((wolf.y - obj.y), 2))
            if temp_dist < dist:
                dist = temp_dist
                index = i
    log = "nearest_sheep({}, {}) was called,".format(
        sheep_list, wolf) + " returned " + str(index) + ", " + str(dist)
    logging.debug(log)
    return index, dist


def sheep_alive(sheep_list):
    count_alive = sum(map(bool, sheep_list))
    log = "sheep_alive({}) was called,".format(sheep_list) + " returned " + str(count_alive)
    logging.debug(log)
    return count_alive


def wolf_move(sheep_list, wolf, wolf_move_dist):
    index, dist = nearest_sheep(sheep_list, wolf)
    if dist <= wolf_move_dist:
        wolf.x = sheep_list[index].x
        wolf.y = sheep_list[index].y
        sheep_list[index] = None
        print("Wolf ate sheep with index: " + str(index))
        logging.info("Wolf ate sheep with index: " + str(index))
    else:
        move_x = ((sheep_list[index].x - wolf.x) / dist) * wolf_move_dist
        move_y = ((sheep_list[index].y - wolf.y) / dist) * wolf_move_dist
        wolf.x += move_x
        wolf.y += move_y
        print("Wolf chose sheep with index: " + str(index))
        logging.info("Wolf chose sheep with index: " + str(index))
    log = "wolf_move({}, {}, {}) was called".format(
        sheep_list, wolf, wolf_move_dist)
    logging.debug(log)


def create_dictionary(round_json, sheep_list, wolf):
    sheep_positions = []
    for obj in sheep_list:
        if obj:
            sheep_positions.append([obj.x, obj.y])
        else:
            sheep_positions.append(None)
    dictionary = {
        "round_no": round_json,
        "wolf_pos": [wolf.x, wolf.y],
        "sheep_pos": sheep_positions
    }
    log = "create_dictionary({}, {}, {}) was called,".format(round_json, sheep_list, wolf) + \
          " returned " + str(dictionary)
    logging.debug(log)
    return dictionary


def to_json(dict_json, directory):
    path_dir = "pos.json"
    if directory:
        path_dir = f"./{directory}/pos.json"

    with open(path_dir, "w") as json_file:
        json.dump(dict_json, json_file, indent=4)
    log = "to_json({}, {}) was called".format(dict_json, directory)
    logging.debug(log)


def to_csv(round_csv, alive, directory):
    path_dir = "alive.csv"
    if directory:
        path_dir = f"./{directory}/alive.csv"

    header_csv = ["Round number", "Number of alive sheep"]

    if round_csv == 1:
        with open(path_dir, "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(header_csv)
            row = [round_csv, alive]
            writer.writerow(row)
    else:
        with open(path_dir, "a") as csv_file:
            writer = csv.writer(csv_file)
            row = [round_csv, alive]
            writer.writerow(row)

    log = "to_csv({}, {}, {}) was called".format(round_csv, alive, directory)
    logging.debug(log)


def is_positive(number):
    try:
        int_number = int(number)
        if int_number <= 0:
            logging.error("%s - given value must be positive!" % number)
            raise argparse.ArgumentTypeError("%s - given value must be positive!" % number)
        log = "is_positive({}) was called,".format(number) + " returned " + str(int_number)
        logging.debug(log)
        return int_number
    except (ValueError, argparse.ArgumentTypeError):
        logging.error("Error in is_positive() function!")
        exit(1)


def parse_config_file(file):
    parser = ConfigParser()
    parser.read(file)
    init_pos_limit = parser.get("Terrain", "InitPosLimit")
    sheep_move_dist = parser.get("Movement", "SheepMoveDist")
    wolf_move_dist = parser.get("Movement", "WolfMoveDist")
    try:
        if float(init_pos_limit) < 0 or float(sheep_move_dist) < 0 or float(wolf_move_dist) < 0:
            logging.error("Not positive number or numbers in config file!")
            raise ValueError("Not positive number or numbers in config file!")
        log = "parse_config_file({}) was called,".format(file) + \
              " returned " + init_pos_limit + ", " + sheep_move_dist + ", " + wolf_move_dist
        logging.debug(log)
        return float(init_pos_limit), float(sheep_move_dist), float(wolf_move_dist)
    except ValueError:
        logging.error("ValueError in parse_config_file() function!")
        exit(1)


def main():
    directory = None
    wait = False
    round_number = 50
    sheep_number = 15
    init_pos_limit = 10.0
    sheep_move_dist = 0.5
    wolf_move_dist = 1.0
    wolf = Wolf(0.0, 0.0)
    sheep_list = []

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", dest="config_file", metavar="FILE", action="store",
                        help="Configuration file.")
    parser.add_argument("-d", "--dir", dest="directory", metavar="DIR", action="store",
                        help="Directory where pos.json and alive.csv are saved.")
    parser.add_argument("-l", "--log", dest="log_level", metavar="LEVEL", action="store", help="Level of events.")
    parser.add_argument("-r", "--rounds", dest="rounds_number", metavar="NUMBER", action="store",
                        help="Number of rounds in simulation.", type=is_positive)
    parser.add_argument("-s", "--sheep", dest="sheep_number", metavar="NUMBER", action="store",
                        help="Number of sheep in simulation.", type=is_positive)
    parser.add_argument("-w", "--wait", action="store_true", help="In each round wait for user input.")

    args = parser.parse_args()

    if args.directory:
        directory = args.directory
        if not os.path.isdir(f"./{directory}"):
            os.mkdir(directory)

    if args.log_level:
        if args.log_level == "DEBUG":
            level = logging.DEBUG
        elif args.log_level == "INFO":
            level = logging.INFO
        elif args.log_level == "WARNING":
            level = logging.WARNING
        elif args.log_level == "ERROR":
            level = logging.ERROR
        elif args.log_level == "CRITICAL":
            level = logging.CRITICAL
        else:
            raise ValueError("Invalid log level!")
        path_dir = "chase.log"
        if directory:
            path_dir = f"./{directory}/chase.log"
        logging.basicConfig(level=level, filename=path_dir, force=True)
        logging.info("New simulation")

    if args.config_file:
        init_pos_limit, sheep_move_dist, wolf_move_dist = parse_config_file(args.config_file)

    if args.rounds_number:
        round_number = args.rounds_number

    if args.sheep_number:
        sheep_number = args.sheep_number

    if args.wait:
        wait = args.wait

    for _ in range(sheep_number):
        random_x = random.uniform(-init_pos_limit, init_pos_limit)
        random_y = random.uniform(-init_pos_limit, init_pos_limit)
        sheep_list.append(Sheep(random_x, random_y))

    dict_list = []

    for i in range(1, round_number + 1):
        if sheep_alive(sheep_list) == 0:
            print("Wolf ate all sheep. The end of simulation.")
            logging.info("Wolf ate all sheep. The end of simulation.")
            break

        print("Round number: " + str(i))
        logging.info("Round number: " + str(i))

        print("Wolf position: " + str(round(wolf.x, 3)) + ", " + str(round(wolf.y, 3)))
        logging.info("Wolf position: " + str(round(wolf.x, 3)) + ", " + str(round(wolf.y, 3)))

        sheep_move(sheep_list, sheep_move_dist)
        wolf_move(sheep_list, wolf, wolf_move_dist)

        print("Alive sheep: " + str(sheep_alive(sheep_list)))
        logging.info("Alive sheep: " + str(sheep_alive(sheep_list)))

        dict_list.append(create_dictionary(i, sheep_list, wolf))
        to_csv(i, sheep_alive(sheep_list), directory)

        if wait:
            input("Press enter to continue...")

    to_json(dict_list, directory)


if __name__ == "__main__":
    main()
