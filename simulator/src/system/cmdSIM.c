/*                                 SUCHAI
 *                      NANOSATELLITE FLIGHT SOFTWARE
 *
 *      Copyright 2020, Carlos Gonzalez Cortes, carlgonz@uchile.cl
 *      Copyright 2020, Tomas Opazo Toro, tomas.opazo.t@gmail.com
 *      Copyright 2020, Matias Ramirez Martinez, nicoram.mt@gmail.com
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "cmdSIM.h"

static const char* tag = "cmdSIM";
static int sim_running = 0;
static pthread_cond_t sim_running_cond = PTHREAD_COND_INITIALIZER;
static pthread_mutex_t sim_running_mutex = PTHREAD_MUTEX_INITIALIZER;

void cmd_sim_init(void)
{
    cmd_add("sim_start", sim_start, "", 0);
    cmd_add("sim_stop", sim_stop, "", 0);
}

void _sim_wait_state(int state)
{
    pthread_mutex_lock(&sim_running_mutex);
    while(state != sim_running)
        pthread_cond_wait(&sim_running_cond, &sim_running_mutex);
    pthread_mutex_unlock(&sim_running_mutex);
}

int _sim_get_state(void)
{
    pthread_mutex_lock(&sim_running_mutex);
    int state = sim_running;
    pthread_mutex_unlock(&sim_running_mutex);
    return state;
}

int sim_start(char* fmt, char* params, int nparams)
{
    pthread_mutex_lock(&sim_running_mutex);
    sim_running = SIM_RUN;
    pthread_cond_broadcast(&sim_running_cond);
    pthread_mutex_unlock(&sim_running_mutex);
    return CMD_OK;
}

int sim_stop(char* fmt, char* params, int nparams)
{
    pthread_mutex_lock(&sim_running_mutex);
    sim_running = SIM_STOP;
    pthread_cond_broadcast(&sim_running_cond);
    pthread_mutex_unlock(&sim_running_mutex);
    return CMD_OK;
}