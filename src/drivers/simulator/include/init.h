/**
 * @file init.h
 * @author Carlos Gonzalez C - carlgonz@uchile.cl
 * @author Matias Ramirez M - nicoram.mt@gmail.com
 * @date 2019
 * @copyright GNU GPL v3
 *
 * Initialization functions
 */

#ifndef SUCHAI_FLIGHT_SOFTWARE_INITI_H
#define SUCHAI_FLIGHT_SOFTWARE_INITI_H

#include "config.h"
#include "utils.h"
#include <stdio.h>
#include <signal.h>

/* system includes */
#include "repoData.h"
#include "repoCommand.h"

/**
 * Performs a clean exit
 *
 * @param signal Int. Signal number
 */
void on_close(int signal);

/**
 * Performs initialization actions
 */
void on_reset(void);

/**
 *
 * @param argc
 * @param argv
 */
void load_config(int argc, char **argv);

#endif //SUCHAI_FLIGHT_SOFTWARE_INITI_H

