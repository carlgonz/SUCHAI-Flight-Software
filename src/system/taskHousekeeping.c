/*                                 SUCHAI
 *                      NANOSATELLITE FLIGHT SOFTWARE
 *
 *      Copyright 2019, Carlos Gonzalez Cortes, carlgonz@uchile.cl
 *      Copyright 2019, Tomas Opazo Toro, tomas.opazo.t@gmail.com
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

#include "taskHousekeeping.h"

static const char *tag = "Housekeeping";

void taskHousekeeping(void *param)
{
    LOGI(tag, "Started");

    uint32_t delay_ms = 1000;               //Task period in [ms]
    unsigned int elapsed_sec = 1;           // Seconds counter
    unsigned int _tle_period = 1;           // Propagate TLE period in seconds
    unsigned int _10sec_check = 10;         // 10[s] condition
    unsigned int _01min_check = 1*60;       // 05[m] condition
    unsigned int _05min_check = 5*60;       // 05[m] condition
    unsigned int _1hour_check = 60*60;      // 01[h] condition

    portTick xLastWakeTime = osTaskGetTickCount();

    while(1)
    {
        osTaskDelayUntil(&xLastWakeTime, delay_ms); //Suspend task

        /* 1 second actions */
        elapsed_sec += 1; //Update seconds counts
        dat_set_system_var(dat_rtc_date_time, (int)dat_get_time());

        if((elapsed_sec % _tle_period) == 0)
        {
            cmd_t *cmd_tle_prop = cmd_get_str("obc_prop_tle");
            cmd_add_params_str(cmd_tle_prop, "0");
            cmd_send(cmd_tle_prop);
        }

        /* 10 seconds actions */
        if((elapsed_sec % _10sec_check) == 0)
        {
            LOGD(tag, "10 sec. check");
            cmd_t *cmd_tm = cmd_get_str("tm_send_status");
            cmd_add_params_var(cmd_tm, 0);
            cmd_send(cmd_tm);
        }

        /* 1 hours actions */
        if((elapsed_sec % _1hour_check) == 0)
        {
            LOGD(tag, "1 hour check");
            cmd_t *cmd_1h = cmd_get_str("drp_add_hrs_alive");
            cmd_add_params_var(cmd_1h, 1); // Add 1hr
            cmd_send(cmd_1h);
        }
    }
}
