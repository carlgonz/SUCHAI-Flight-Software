/*                                 SUCHAI
 *                      NANOSATELLITE FLIGHT SOFTWARE
 *
 *      Copyright 2019, Carlos Gonzalez Cortes, carlgonz@uchile.cl
 *      Copyright 2019, Matias Ramirez Martinez, nicoram.mt@gmail.com
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

#include "init.h"

static const char *tag = "on_reset";

void on_close(int signal)
{
    dat_repo_close();
    cmd_repo_close();

    LOGI(tag, "Exit system!");
    exit(signal);
}

void on_reset(void)
{
    /* Register INT/TERM signals */
    struct sigaction act;
    act.sa_handler = on_close;
    sigaction(SIGINT, &act, NULL);  // Register CTR+C signal handler
    sigaction(SIGTERM, &act, NULL);
}

void load_config(int argc, char **argv)
{
    SCH_COMM_ZMQ_OUT = _SCH_COMM_ZMQ_OUT;
    SCH_COMM_ZMQ_IN = _SCH_COMM_ZMQ_IN;

    if(argc > 2)
    {
        SCH_COMM_ZMQ_IN = argv[1];
        SCH_COMM_ZMQ_OUT = argv[2];
    }
    printf("ZMQ: %s; %s\n", SCH_COMM_ZMQ_IN, SCH_COMM_ZMQ_OUT);

    SCH_DEVICE_ID = _SCH_DEVICE_ID;
    SCH_EPS_ADDRESS = _SCH_EPS_ADDRESS;
    SCH_TRX_ADDRESS = _SCH_TRX_ADDRESS;
    SCH_TNC_ADDRESS = _SCH_TNC_ADDRESS;
    if(argc > 6)
    {
        SCH_DEVICE_ID = (int)strtol(argv[3], NULL, 10);
        SCH_EPS_ADDRESS = (int)strtol(argv[6], NULL, 10);
        SCH_TRX_ADDRESS = (int)strtol(argv[5], NULL, 10);
        SCH_TNC_ADDRESS = (int)strtol(argv[4], NULL, 10);
    }
    printf("OBC: %d, EPS: %d, TRX: %d, TNC: %d", SCH_DEVICE_ID,
           SCH_EPS_ADDRESS, SCH_TRX_ADDRESS, SCH_TNC_ADDRESS);

}
