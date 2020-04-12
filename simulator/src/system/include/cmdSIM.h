/**
 * @file  cmdSIM.h
 * @author Carlos Gonzalez C - carlgonz@uchile.cl
 * @author Camilo Rojas C - camrojas@uchile.cl
 * @date 2020
 * @copyright GNU GPL v3
 *
 * This header have definitions of commands related to the flight software
 * simulator
 */

#ifndef _CMDSIM_H
#define _CMDSIM_H

#define SIM_STOP 0
#define SIM_RUN 1

#include "pthread.h"

#include "repoData.h"
#include "repoCommand.h"

void cmd_sim_init(void);

/**
 * Wait the simulation change to the given status. Blocking.
 * @param state
 */
void _sim_wait_state(int state);
int _sim_get_state(void);

/**
 * Set simulation state to running (1)
 */
int sim_start(char* fmt, char* params, int nparams);

/**
 * Set simulation state to stop (0)
 */
int sim_stop(char* fmt, char* params, int nparams);

#endif //_CMDSIM_H
